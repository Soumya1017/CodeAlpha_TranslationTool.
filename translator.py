import os
import time

import requests
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests

# {'afrikaans': 'af', 'hindi': 'hi', ...} (language name -> language code)
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)

BACKUP_URL = "https://api.mymemory.translated.net/get"
ALT_URL = "https://translate.googleapis.com/translate_a/single"
MAX_BYTES = 450  # the backup service accepts at most 500 bytes per request

# MyMemory is more accurate with regional codes
REGIONAL = {
    "hi": "hi-IN", "kn": "kn-IN", "ta": "ta-IN", "te": "te-IN", "ml": "ml-IN",
    "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-PK",
    "en": "en-GB",
}

# Unicode ranges used to check that an answer is in the right script
SCRIPT_RANGES = {
    "kn": (0x0C80, 0x0CFF), "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
    "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F), "ml": (0x0D00, 0x0D7F),
    "bn": (0x0980, 0x09FF), "gu": (0x0A80, 0x0AFF), "pa": (0x0A00, 0x0A7F),
}

_google_cache = {}  # only Google answers are remembered, never backup answers


def split_text(text, max_bytes=MAX_BYTES):
    """Cut text into pieces that fit the backup service's size limit."""
    pieces, current = [], ""
    for word in text.split():
        while len(word.encode("utf-8")) > max_bytes:  # one extremely long word
            if current:
                pieces.append(current)
                current = ""
            pieces.append(word[:100])
            word = word[100:]
        candidate = f"{current} {word}".strip()
        if len(candidate.encode("utf-8")) > max_bytes:
            pieces.append(current)
            candidate = word
        current = candidate
    if current:
        pieces.append(current)
    return pieces


def wrong_script(result, target):
    """True if the result is clearly not written in the target language's script."""
    if target not in SCRIPT_RANGES:
        return False
    low, high = SCRIPT_RANGES[target]
    letters = [c for c in result if c.isalpha()]
    if not letters:
        return False
    right = sum(low <= ord(c) <= high for c in letters)
    return right / len(letters) < 0.5


def translate_google_alt(text, source, target):
    """Second Google endpoint, used when the first one is blocked."""
    reply = requests.post(
        ALT_URL,
        params={"client": "gtx", "sl": source, "tl": target, "dt": "t"},
        data={"q": text},
        timeout=15,
    )
    reply.raise_for_status()
    data = reply.json()
    return "".join(part[0] for part in data[0] if part[0])


def translate_backup(text, source, target):
    """Backup service (MyMemory). Returns (translation, lowest match score)."""
    src = "Autodetect" if source == "auto" else REGIONAL.get(source, source)
    pair = f"{src}|{REGIONAL.get(target, target)}"
    params = {"langpair": pair}
    email = os.environ.get("MYMEMORY_EMAIL")
    if email:
        params["de"] = email
    results, lowest = [], 1.0
    for piece in split_text(text):
        reply = requests.get(BACKUP_URL, params={**params, "q": piece}, timeout=15)
        data = reply.json()
        info = data.get("responseData") or {}
        translated = info.get("translatedText") or ""
        if "MYMEMORY WARNING" in translated or str(data.get("responseStatus")) != "200":
            raise RuntimeError(
                data.get("responseDetails") or translated or "The backup service refused the request."
            )
        lowest = min(lowest, float(info.get("match") or 0))
        results.append(translated)
    return " ".join(results), lowest


def translate_text(text, source, target):
    """Returns (translation, service name). source can be 'auto'."""
    text = text.strip()
    if not text:
        return "", ""
    key = (text, source, target)
    if key in _google_cache:
        return _google_cache[key], "Google Translate"

    # 1) normal Google route
    for attempt in range(2):
        try:
            result = GoogleTranslator(source=source, target=target).translate(text)
            _google_cache[key] = result
            return result, "Google Translate"
        except TooManyRequests:
            time.sleep(2)

    # 2) second Google endpoint
    try:
        result = translate_google_alt(text, source, target)
        if result:
            _google_cache[key] = result
            return result, "Google Translate"
    except Exception:
        pass

    # 3) last resort: MyMemory, but never show an answer in the wrong script
    result, score = translate_backup(text, source, target)
    if wrong_script(result, target):
        raise RuntimeError(
            "Google is blocking this connection and the backup service returned the "
            "wrong language. Please try again on a different network (for example a phone hotspot)."
        )
    label = "MyMemory (backup service)"
    if score < 0.6:
        label += " - low confidence"
    return result, label