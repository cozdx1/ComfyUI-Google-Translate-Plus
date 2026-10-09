import importlib.util
import hashlib
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

    def test_quoted_parentheses_translate_without_changing_dialogue(self):
        for opening, closing in [('"', '"'), ('“', '”'), ('「', '」'), ('『', '』')]:
            text = opening + '그래서, (잠시 멈추고) 오늘은 뭐 할 건데? 룰?' + closing
            seen = []
            def transport(value, source, target):
                seen.append(value)
                return value.replace('잠시 멈추고', 'pauses briefly')
            result = translator.translate(text, 'ko', 'en', transport=transport)
            self.assertEqual(result, text.replace('잠시 멈추고', 'pauses briefly'))
            self.assertIn('잠시 멈추고', seen[0])
            self.assertNotIn('오늘은 뭐 할 건데?', seen[0])

    def test_multiple_nested_and_escaped_parentheses(self):
        text = r'"안녕 (작게 (웃으며)) 그리고 (손을 흔들며) 끝 \(그대로\) () (닫히지 않음"'
        result = translator.translate(text, 'ko', 'en', transport=lambda value, *_: value.replace('작게 (웃으며)', 'quietly (smiling)').replace('손을 흔들며', 'waving'))
        self.assertEqual(result, text.replace('작게 (웃으며)', 'quietly (smiling)').replace('손을 흔들며', 'waving'))

    def test_backticks_keep_parentheses_literal(self):
        text = '"대사 `문구 (그대로)` (웃으며 `이름`) 끝" ```대사 (그대로)```'
        result = translator.translate(text, 'ko', 'en', transport=lambda value, *_: value.replace('웃으며', 'smiling').replace('그대로', 'changed').replace('이름', 'changed'))
        self.assertEqual(result, text.replace('웃으며', 'smiling'))
        literal = '`대사 (그대로)`'
        self.assertEqual(translator.translate(literal, 'ko', 'en', transport=lambda *_: self.fail('Network called')), literal)

    def test_parentheses_exception_respects_modes(self):
        text = '"대사 (웃으며)"'
        for mode in ['Quotes + backticks', 'Quotes only']:
            self.assertEqual(translator.translate(text, 'ko', 'en', mode, transport=lambda value, *_: value.replace('대사', 'Speech').replace('웃으며', 'smiling')), '"대사 (smiling)"')
        for mode in ['Backticks only', 'None']:
            self.assertEqual(translator.translate(text, 'ko', 'en', mode, transport=lambda value, *_: value.replace('대사', 'Speech').replace('웃으며', 'smiling')), '"Speech (smiling)"')

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

    async def test_queue_refreshes_preview_saved_before_parentheses_change(self):
        module = self.module
        text = '"안녕 (웃으며)"'
        def old_signature(value, source, target, protection):
            return hashlib.sha256(json.dumps([value, source, target, protection], ensure_ascii=False).encode('utf-8')).hexdigest()
        state = json.dumps({'input': old_signature(text, 'ko', 'en', 'Quotes + backticks'),
                            'output': old_signature(text, '', '', '')})
        with patch.object(module, 'translate', return_value='"안녕 (smiling)"') as network:
            result = await module.GoogleTranslatePlus().output_translation(module._defaults['ko'], module._defaults['en'], 'Quotes + backticks', text, text, state)
            self.assertEqual(network.call_count, 1)
            self.assertEqual(result['result'], ('"안녕 (smiling)"',))


if __name__ == '__main__':
    unittest.main()
