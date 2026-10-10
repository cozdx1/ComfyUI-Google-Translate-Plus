import asyncio
import json
import logging
from pathlib import Path

from aiohttp import web
from server import PromptServer

from .translator import BACKENDS, MODES, signature, translate

_languages = json.loads((Path(__file__).parent / "languages.json").read_text(encoding="utf-8"))
_codes = {f"{name} [{code}]": code for code, name in _languages["target"].items()}
_labels = sorted(_codes, key=str.casefold)
_auto = "자동 감지 [auto]"
_source_codes = {_auto: "auto", **{f"{name} [{code}]": code for code, name in _languages["source"].items() if code != "auto"}}
_source_labels = [_auto] + sorted((label for label in _source_codes if label != _auto), key=str.casefold)
_defaults = {code: label for label, code in _codes.items()}


class GoogleTranslatePlus:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "source_language": (_source_labels, {"default": _auto, "tooltip": "Language of the source text. Auto-detect identifies it automatically."}),
            "target_language": (_labels, {"default": _defaults["en"], "tooltip": "Language to translate the source text into."}),
            "protection": (MODES, {"default": MODES[0], "tooltip": "Preserve quotes and backticks. Text inside parentheses in quotes is translated."}),
            "text": ("STRING", {"multiline": True, "default": "", "tooltip": "Enter the source text. Queue translates automatically; Translate previews the result before running."}),
            "translated_text": ("STRING", {"multiline": True, "default": "", "tooltip": "Read-only translation result."}),
            "translation_state": ("STRING", {"default": ""}),
        }, "optional": {
            "backend": (BACKENDS, {"default": "Google", "tooltip": "Translation engine. Local OPUS-MT uses CPU only and supports Korean to English."}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("translated_text",)
    FUNCTION = "output_translation"
    CATEGORY = "cozdx1/translation"
    DESCRIPTION = "Translate prompts with Google or local OPUS-MT on Queue. Use Translate to preview the result. Preserve quoted text and backticks."

    async def output_translation(self, source_language, target_language, protection, text,
                           translated_text, translation_state, backend="Google"):
        expected = signature(text, _source_codes[source_language], _codes[target_language], protection, backend)
        try:
            state = json.loads(translation_state)
        except (ValueError, TypeError):
            state = {}
        if not isinstance(state, dict):
            state = {}
        if state.get("input") == expected and state.get("output") == signature(translated_text, "", "", ""):
            result = translated_text
        else:
            result = await asyncio.to_thread(translate, text, _source_codes[source_language], _codes[target_language], protection,
                                           **({"backend": backend} if backend != "Google" else {}))
        saved_state = json.dumps({"input": expected, "output": signature(result, "", "", "")})
        return {"ui": {
            "translated_text": [result], "translation_state": [saved_state],
            "input_snapshot": [{"text": text, "source_language": source_language,
                                "target_language": target_language, "protection": protection, "backend": backend}],
        }, "result": (result,)}


@PromptServer.instance.routes.post("/cozdx1/google-translate-plus/translate")
async def translate_manual(request):
    try:
        data = await request.json()
        text = data["text"]
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        source = _source_codes[data["source_language"]]
        target = _codes[data["target_language"]]
        protection = data["protection"]
        backend = data.get("backend", "Google")
        result = await asyncio.to_thread(translate, text, source, target, protection,
                                       **({"backend": backend} if backend != "Google" else {}))
        state = json.dumps({"input": signature(text, source, target, protection, backend),
                            "output": signature(result, "", "", "")})
        return web.json_response({"text": result, "state": state})
    except (KeyError, ValueError, TypeError) as error:
        code = getattr(error, "code", "")
        return web.json_response({"error": str(error), "code": code}, status=429 if code == "rate_limit" else 400)
    except Exception as error:
        # Do not log prompt text or request URLs (they contain user text).
        logging.warning("Google Translate Plus request failed (%s)", type(error).__name__)
        return web.json_response({"error": "Could not connect to Google Translate. Try again later.", "code": "connection"}, status=502)


NODE_CLASS_MAPPINGS = {"GoogleTranslatePlus": GoogleTranslatePlus}
NODE_DISPLAY_NAME_MAPPINGS = {"GoogleTranslatePlus": "[cozdx1] Google Translate Plus"}
WEB_DIRECTORY = "./web"
