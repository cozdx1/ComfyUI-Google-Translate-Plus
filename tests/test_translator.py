import importlib.util
import json
from pathlib import Path
import re
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import translator


class ProtectionTests(unittest.TestCase):
    def test_multiple_literals_exact(self):
        text = '여성이 "좋은 아침~"이라고 말하고 `주현 씨`를 부른다. “안녕”'
        seen = []
        def transport(value, source, target):
            seen.append(value)
            return value.replace('여성이', 'The woman').lower()
        result = translator.translate(text, 'ko', 'en', transport=transport)
        for literal in ['"좋은 아침~"', '`주현 씨`', '“안녕”']:
            self.assertIn(literal, result)
            self.assertNotIn(literal, seen[0])

    def test_multiline_nested_escaped(self):
        text = '```한글\n"안녕"``` 뒤 "그가 \\"안녕\\"이라고"'
        spans = translator.protected_spans(text, translator.MODES[0])
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0][2], '```한글\n"안녕"```')

    def test_lost_or_duplicated_marker_rejected(self):
        for transform in [lambda text: '', lambda text: text + text]:
            with self.assertRaisesRegex(ValueError, 'protected-text marker'):
                translator.translate('말한다 "그대로"', 'ko', 'en', transport=lambda t, s, d: transform(t))

    def test_unclosed_rejected(self):
        for text in ['말한다 "안녕', '말한다 `안녕', '말한다 ```안녕']:
            with self.assertRaisesRegex(ValueError, 'not closed'):
                translator.translate(text, 'ko', 'en', transport=lambda *args: self.fail('Network called'))

    def test_protected_only_no_network(self):
        text = ' "좋은 아침" `안녕` '
        self.assertEqual(translator.translate(text, 'ko', 'en', transport=lambda *args: self.fail('Network called')), text)

    def test_modes(self):
        text = '"안녕" `주현`'
        self.assertEqual(len(translator.protected_spans(text, 'Quotes only')), 1)
        self.assertEqual(len(translator.protected_spans(text, 'Backticks only')), 1)
        self.assertEqual(len(translator.protected_spans(text, 'None')), 0)

    def test_limit_not_truncation(self):
        with self.assertRaisesRegex(ValueError, '5,000'):
            translator.translate('a' * 5001, 'ko', 'en')

    def test_cache(self):
        translator._cache.clear()
        with patch.object(translator, 'google_translate', return_value='Hello') as network:
            self.assertEqual(translator.translate('안녕', 'ko', 'en'), 'Hello')
            self.assertEqual(translator.translate('안녕', 'ko', 'en'), 'Hello')
            self.assertEqual(network.call_count, 1)


class NodeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        routes = types.SimpleNamespace(post=lambda path: lambda handler: handler)
        sys.modules['server'] = types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=types.SimpleNamespace(routes=routes)))
        spec = importlib.util.spec_from_file_location('google_translate_plus_test', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    async def test_queue_reuses_valid_preview(self):
        module = self.module
        state = json.dumps({'input': module.signature('안녕', 'ko', 'en', 'Quotes + backticks'),
                            'output': module.signature('Hello', '', '', '')})
        args = [module._defaults['ko'], module._defaults['en'], 'Quotes + backticks', '안녕', 'Hello', state]
        with patch.object(module, 'translate', side_effect=AssertionError('Queue requested network')):
            result = await module.GoogleTranslatePlus().output_translation(*args)
            self.assertEqual(result['result'], ('Hello',))
            self.assertEqual(result['ui']['translated_text'], ['Hello'])

    async def test_queue_translates_without_preview(self):
        module = self.module
        args = [module._auto, module._defaults['en'], 'Quotes + backticks', '안녕', '', '']
        with patch.object(module, 'translate', return_value='Hello') as network:
            result = await module.GoogleTranslatePlus().output_translation(*args)
            network.assert_called_once_with('안녕', 'auto', 'en', 'Quotes + backticks')
            self.assertEqual(result['result'], ('Hello',))
            self.assertEqual(result['ui']['input_snapshot'][0]['text'], '안녕')
            state = json.loads(result['ui']['translation_state'][0])
            self.assertEqual(state['input'], module.signature('안녕', 'auto', 'en', 'Quotes + backticks'))

    async def test_queue_refreshes_stale_or_tampered_preview(self):
        module = self.module
        state = json.dumps({'input': module.signature('안녕', 'ko', 'en', 'Quotes + backticks'),
                            'output': module.signature('Hello', '', '', '')})
        for text, old_result, saved in [('변경된 원문', 'Hello', state), ('안녕', 'tampered', state), ('안녕', '', '[]')]:
            with self.subTest(text=text, saved=saved), patch.object(module, 'translate', return_value='Fresh') as network:
                result = await module.GoogleTranslatePlus().output_translation(module._defaults['ko'], module._defaults['en'], 'Quotes + backticks', text, old_result, saved)
                self.assertEqual(result['result'], ('Fresh',))
                self.assertEqual(network.call_count, 1)

    async def test_queue_keeps_protected_dialogue(self):
        module = self.module
        with patch.object(module.translator, 'google_translate', side_effect=lambda value, source, target: value.replace('말한다', 'She says')):
            result = await module.GoogleTranslatePlus().output_translation(module._auto, module._defaults['en'], 'Quotes + backticks', '말한다 "좋은 아침"', '', '')
            self.assertEqual(result['result'], ('She says "좋은 아침"',))


if __name__ == '__main__':
    unittest.main()
