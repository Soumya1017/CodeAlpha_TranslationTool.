from functools import lru_cache
from io import BytesIO

from gtts import gTTS
from gtts.lang import tts_langs

# {'hi': 'Hindi', 'kn': 'Kannada', ...} (languages that can be spoken)
SPEECH_LANGUAGES = tts_langs()


@lru_cache(maxsize=64)  # the same sentence is not generated twice
def text_to_speech(text, lang):
    """Return the spoken text as MP3 bytes."""
    buffer = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buffer)
    return buffer.getvalue()