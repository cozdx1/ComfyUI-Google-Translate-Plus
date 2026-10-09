"""Google web translation with fail-closed literal protection. No ML dependencies."""
import hashlib
import json
import re
import threading
import uuid
from collections import OrderedDict
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MODES = ["Quotes + backticks", "Quotes only", "Backticks only", "None"]
_cache = OrderedDict()
_lock = threading.Lock()


class TranslationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def signature(text, source, target, protection):
    # Invalidate previews saved before quoted parentheses became translatable.
    payload = json.dumps(["quoted-parentheses-v1", text, source, target, protection], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def quoted_spans(text, start, end, mode):
    """Protect a quote, leaving balanced parenthetical contents translatable."""
    inner_start, inner_end = start + 1, end - 1
    code_spans = []
    if mode == MODES[0]:
        code_spans = [(inner_start + a, inner_start + b, literal)
                      for a, b, literal in protected_spans(text[inner_start:inner_end], "Backticks only")]
    code_ends = {a: b for a, b, _ in code_spans}
    bodies, depth, i = [], 0, inner_start
    while i < inner_end:
        if text[i] == '\\':
            i += 2
            continue
        if i in code_ends:
            i = code_ends[i]
            continue
        if text[i] == '(':
            if depth == 0:
                body_start = i + 1
            depth += 1
        elif text[i] == ')' and depth:
            depth -= 1
            if depth == 0 and body_start < i:
                bodies.append((body_start, i))
        i += 1
    spans, cursor = [], start
    for body_start, body_end in bodies:
        spans.append((cursor, body_start, text[cursor:body_start]))
        spans.extend(span for span in code_spans if body_start <= span[0] and span[1] <= body_end)
        cursor = body_end
    spans.append((cursor, end, text[cursor:end]))
    return spans


def protected_spans(text, mode):
    if mode not in MODES:
        raise ValueError("Unknown protection mode")
    delimiters = {}
    if mode in MODES[:2]:
        delimiters.update({'"': '"', '“': '”', '「': '」', '『': '』'})
    if mode in (MODES[0], MODES[2]):
        delimiters['`'] = '`'
    spans = []
    i = 0
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        if text[i] not in delimiters:
            i += 1
            continue
        opening = '```' if text.startswith('```', i) and '`' in delimiters else text[i]
        closing = '```' if opening == '```' else delimiters[opening]
        j = i + len(opening)
        while j < len(text):
            if text[j] == '\\':
                j += 2
            elif text.startswith(closing, j):
                end = j + len(closing)
                if opening.startswith('`'):
                    spans.append((i, end, text[i:end]))
                else:
                    spans.extend(quoted_spans(text, i, end, mode))
                i = end
                break
            else:
                j += 1
        else:
            raise TranslationError("unclosed", "A protected delimiter is not closed. Check the pairs of quotes and backticks.")
    return spans


def google_translate(text, source, target):
    query = urlencode(dict(client="gtx", sl=source, tl=target, dt="t", q=text))
    request = Request("https://translate.googleapis.com/translate_a/single?" + query,
                      headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=25) as response:
        payload = json.load(response)
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        raise TranslationError("response", "Google returned an unexpected translation response.")
    result = ''.join(part[0] for part in payload[0] if part and isinstance(part[0], str))
    if not result.strip():
        raise TranslationError("response", "Google returned an empty translation.")
    return result


def translate(text, source, target, protection=MODES[0], transport=None):
    if len(text) > 5000:
        raise TranslationError("limit", "Translate up to 5,000 characters at once. The source text is not truncated.")
    spans = protected_spans(text, protection)
    if not text.strip():
        return text
    key = signature(text, source, target, protection)
    if transport is None:
        with _lock:
            if key in _cache:
                _cache.move_to_end(key)
                return _cache[key]
    nonce = uuid.uuid4().hex[:12].upper()
    pieces, literals, outside, cursor = [], [], [], 0
    for index, (start, end, literal) in enumerate(spans):
        token = f"ZXQKEEP{nonce}N{index}QXZ"
        outside.append(text[cursor:start])
        pieces.extend((outside[-1], token))
        literals.append((token, literal))
        cursor = end
    outside.append(text[cursor:])
    pieces.append(outside[-1])
    # A protected-only input needs no network request.
    if spans and not ''.join(outside).strip():
        return text
    result = (transport or google_translate)(''.join(pieces), source, target)
    replacements = {}
    for token, literal in literals:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        if len(pattern.findall(result)) != 1:
            raise TranslationError("marker", "Google changed a protected-text marker. The result was rejected. Try again.")
        replacements[token.lower()] = literal
    if literals:
        # One substitution pass: restored user text is never interpreted as a marker.
        pattern = re.compile('|'.join(re.escape(t) for t, _ in literals), re.IGNORECASE)
        result = pattern.sub(lambda match: replacements[match.group().lower()], result)
    if transport is None:
        with _lock:
            _cache[key] = result
            _cache.move_to_end(key)
            while len(_cache) > 128:
                _cache.popitem(last=False)
    return result
