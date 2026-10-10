"""Offline Korean-to-English translation. Loads lazily and uses CPU only."""
import re
import threading
from pathlib import Path

from .translator import TranslationError, protected_spans

_model = None
_model_lock = threading.Lock()


def _load_model():
    global _model
    with _model_lock:
        if _model is not None:
            return _model
        try:
            import ctranslate2
            import sentencepiece
        except (ImportError, OSError):
            raise TranslationError("local_setup", "Install ctranslate2 and sentencepiece in ComfyUI's Python environment.") from None
        import folder_paths
        path = Path(folder_paths.models_dir) / "translation" / "opus-mt-tc-big-ko-en-int8"
        required = ["model.bin", "config.json", "source.spm", "target.spm", "source_vocabulary.json", "target_vocabulary.json"]
        if not all((path / name).is_file() for name in required):
            raise TranslationError("local_setup", "Local OPUS-MT model is missing. Install it in models/translation/opus-mt-tc-big-ko-en-int8.")
        try:
            engine = ctranslate2.Translator(str(path), device="cpu", compute_type="int8", intra_threads=4, inter_threads=1)
            source = sentencepiece.SentencePieceProcessor(model_file=str(path / "source.spm"))
            target = sentencepiece.SentencePieceProcessor(model_file=str(path / "target.spm"))
        except Exception:
            raise TranslationError("local_setup", "Could not load the local OPUS-MT CPU model.") from None
        _model = engine, source, target
        return _model


def _translate_segment(text, engine, source, target):
    # Preserve line breaks and boundary whitespace; split long inputs without
    # CTranslate2 silently truncating them at its default input-token limit.
    pieces = []
    for line in re.split(r"(\r\n|\r|\n)", text):
        if not line.strip():
            pieces.append(line)
            continue
        match = re.fullmatch(r"(\s*)(.*?)(\s*)", line, re.DOTALL)
        leading, body, trailing = match.groups()
        if not re.search(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]", body):
            pieces.append(line)
            continue
        translated = []
        # Sentence boundaries keep ordinary prompts in complete context.
        for sentence in re.split(r"(?<=[.!?。！？])\s+", body):
            tokens = source.encode(sentence, out_type=str)
            for start in range(0, len(tokens), 400):
                try:
                    result = engine.translate_batch(
                        [tokens[start:start + 400]], beam_size=4,
                        max_input_length=0, max_decoding_length=1024,
                        replace_unknowns=True,
                    )[0]
                except (RuntimeError, IndexError):
                    raise TranslationError("local_output", "Local translation failed. Split the source into shorter sentences.") from None
                # CTranslate2 strips EOS; reaching the cap means incomplete output.
                if not result.hypotheses or len(result.hypotheses[0]) >= 1024:
                    raise TranslationError("local_output", "Local translation did not finish. Split the source into shorter sentences.")
                value = target.decode([token for token in result.hypotheses[0] if token not in ("</s>", "<pad>")]).strip()
                if not value:
                    raise TranslationError("local_output", "The local model returned an empty translation.")
                translated.append(value)
        pieces.append(leading + " ".join(translated) + trailing)
    return "".join(pieces)


def translate_local(text, source, target, protection):
    if len(text) > 5000:
        raise TranslationError("limit", "Translate up to 5,000 characters at once. The source text is not truncated.")
    if source not in ("auto", "ko", "en") or target != "en":
        raise TranslationError("local_language", "Local OPUS-MT supports Korean to English only. Use Korean or Auto-detect as source and English as target.")
    spans = protected_spans(text, protection)
    if not text.strip() or source == target:
        return text
    # Never send placeholders to the small translation model. Translate the
    # gaps and restore protected literals byte-for-byte, including delimiters.
    pieces, cursor, model = [], 0, None
    for start, end, literal in [*spans, (len(text), len(text), "")]:
        segment = text[cursor:start]
        if re.search(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]", segment):
            if model is None:
                model = _load_model()
            pieces.append(_translate_segment(segment, *model))
        else:
            pieces.append(segment)
        pieces.append(literal)
        cursor = end
    return "".join(pieces)
