import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType("offline_translation_tests")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
for name in ("translator", "local_translation"):
    spec = importlib.util.spec_from_file_location(package.__name__ + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
translator = sys.modules[package.__name__ + ".translator"]
local = sys.modules[package.__name__ + ".local_translation"]


class OfflineTests(unittest.TestCase):
    def setUp(self):
        translator._cache.clear()

    def test_protection_and_parentheses_without_google(self):
        text = '설명\n"대사 (웃으며 `이름`) 끝" `그대로 (보존)`'
        seen = []
        def segment(value, *model):
            seen.append(value)
            return value.replace('설명', 'Description').replace('웃으며', 'smiling')
        with patch.object(local, '_load_model', return_value=(None, None, None)), patch.object(local, '_translate_segment', side_effect=segment), patch.object(translator, 'google_translate', side_effect=AssertionError('Network called')):
            result = translator.translate(text, 'ko', 'en', backend=translator.BACKENDS[1])
        self.assertEqual(result, 'Description\n"대사 (smiling `이름`) 끝" `그대로 (보존)`')
        self.assertNotIn('대사', ''.join(seen))
        self.assertNotIn('이름', ''.join(seen))

    def test_unsupported_languages_do_not_fallback_to_google(self):
        for source, target in [('ko', 'ja'), ('ja', 'en'), ('fr', 'en')]:
            with patch.object(translator, 'google_translate', side_effect=AssertionError('Network called')):
                with self.assertRaises(translator.TranslationError) as caught:
                    translator.translate('원문', source, target, backend=translator.BACKENDS[1])
                self.assertEqual(caught.exception.code, 'local_language')

    def test_local_cache_and_google_cache_are_separate(self):
        with patch.object(translator, 'google_translate', return_value='Google result'), patch.object(local, 'translate_local', return_value='Local result') as cpu:
            self.assertEqual(translator.translate('안녕', 'ko', 'en'), 'Google result')
            for _ in range(2):
                self.assertEqual(translator.translate('안녕', 'ko', 'en', backend=translator.BACKENDS[1]), 'Local result')
            self.assertEqual(cpu.call_count, 1)
        self.assertNotEqual(translator.signature('안녕', 'ko', 'en', 'None'), translator.signature('안녕', 'ko', 'en', 'None', translator.BACKENDS[1]))

    def test_protected_only_and_english_do_not_load_model(self):
        for text in ['"한글" `그대로`', 'A man waves.\n  No zoom.']:
            with patch.object(local, '_load_model', side_effect=AssertionError('Unnecessary model load')):
                self.assertEqual(local.translate_local(text, 'auto', 'en', 'Quotes + backticks'), text)

    def test_token_limit_splits_without_losing_tokens(self):
        batches = []
        class Engine:
            def translate_batch(self, batch, **options):
                batches.extend(batch)
                self.options = options
                return [types.SimpleNamespace(hypotheses=[['translated']])]
        engine = Engine()
        source = types.SimpleNamespace(encode=lambda *args, **kwargs: list(range(901)))
        target = types.SimpleNamespace(decode=lambda tokens: 'Translated')
        output = local._translate_segment('  한글\r\n', engine, source, target)
        self.assertEqual([len(batch) for batch in batches], [400, 400, 101])
        self.assertEqual([token for batch in batches for token in batch], list(range(901)))
        self.assertEqual(engine.options['max_input_length'], 0)
        self.assertEqual(output, '  Translated Translated Translated\r\n')

    def test_decode_cap_rejected(self):
        engine = types.SimpleNamespace(translate_batch=lambda *a, **kw: [types.SimpleNamespace(hypotheses=[['x'] * 1024])])
        source = types.SimpleNamespace(encode=lambda *args, **kwargs: ['x'])
        with self.assertRaises(translator.TranslationError) as caught:
            local._translate_segment('한글', engine, source, None)
        self.assertEqual(caught.exception.code, 'local_output')
