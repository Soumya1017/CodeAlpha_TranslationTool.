import json

import streamlit as st
import streamlit.components.v1 as components

from speech import SPEECH_LANGUAGES, text_to_speech
from translator import LANGUAGES, translate_text

st.set_page_config(page_title="Language Translator", page_icon="🌐")
st.title("🌐 Language Translator")
st.caption("Type your text, choose the languages, and click Translate.")

# display name -> language code, e.g. {"Hindi": "hi"}
codes = {name.title(): code for name, code in LANGUAGES.items()}
names = sorted(codes)


def copy_button(text):
    components.html(f"""
    <button id="c" style="padding:6px 14px;border-radius:6px;border:1px solid #ccc;cursor:pointer;">📋 Copy</button>
    <script>
    const text = {json.dumps(text)};
    document.getElementById("c").onclick = async () => {{
        try {{ await navigator.clipboard.writeText(text); }}
        catch (e) {{
            const t = document.createElement("textarea");
            t.value = text; document.body.appendChild(t);
            t.select(); document.execCommand("copy"); t.remove();
        }}
        document.getElementById("c").innerText = "✅ Copied";
    }};
    </script>
    """, height=45)


col1, col2 = st.columns(2)
with col1:
    source_name = st.selectbox("From", ["Auto-detect"] + names)
with col2:
    target_name = st.selectbox("To", names, index=names.index("Hindi"))

text = st.text_area("Text to translate", height=150, max_chars=5000)

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text first.")
    else:
        source = "auto" if source_name == "Auto-detect" else codes[source_name]
        target = codes[target_name]
        try:
            with st.spinner("Translating..."):
                result, service = translate_text(text, source, target)
            st.session_state.result = result
            st.session_state.service = service
            st.session_state.target_code = target  # remember it for the Listen button
        except Exception as error:
            st.session_state.pop("result", None)
            st.error(f"Translation failed. Check your internet connection and try again. ({error})")

if st.session_state.get("result"):
    st.subheader("Translation")
    st.code(st.session_state.result, language=None, wrap_lines=True)
    copy_button(st.session_state.result)
    st.caption(f"Translated by {st.session_state.service}")
    if "backup" in st.session_state.service:
        st.warning("Google is limiting this connection, so a backup service was used. "
                   "Accuracy may be lower, especially for Indian languages like Kannada.")

    lang = st.session_state.target_code
    if lang in SPEECH_LANGUAGES:
        if st.button("🔊 Listen"):
            try:
                with st.spinner("Preparing audio..."):
                    audio = text_to_speech(st.session_state.result, lang)
                st.audio(audio, format="audio/mp3", autoplay=True)
            except Exception as error:
                st.error(f"Could not create the audio. Check your internet connection. ({error})")
    else:
        st.caption("Speech is not available for this language.")