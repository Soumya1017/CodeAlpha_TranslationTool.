# CodeAlpha_TranslationTool

A language translation tool built for the CodeAlpha AI internship (Task 1). Type text, choose the source and target languages, and get the translation on screen. It can also copy the result and read it aloud.

## Features
- Translate between 130+ languages, or let the tool auto-detect the source language
- Streamlit web interface with From and To dropdowns
- Copy button under the result that copies the translation to the clipboard
- Text-to-speech: a Listen button reads the translation aloud (available for about 65 of the languages)
- Shows which service produced the translation
- Checks that the answer is written in the correct script and refuses wrong-language results
- Clear error messages instead of crashes when the internet or a service fails

## How it works
1. The user types text and picks the languages in the Streamlit page (`app.py`).
2. `translator.py` sends the text to Google Translate through the **deep-translator** library and returns the result.
3. If Google blocks the first route, the tool tries a second Google route, and only then uses the backup service **MyMemory**. It always tells the user which service answered.
4. Backup answers written in the wrong script are rejected, and the user sees a clear message instead of a wrong translation.
5. `speech.py` turns the translation into spoken audio with **gTTS** when the Listen button is clicked.

## Project structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit interface |
| `translator.py` | Translation logic: Google (two routes), with a MyMemory backup |
| `speech.py` | Text-to-speech |
| `requirements.txt` | Libraries to install |

## Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

## Limitations
- Google Translate is used through the free deep-translator library and a public Google endpoint, not the official paid API. Google can temporarily block an internet connection that sends many requests.
- The backup service (MyMemory) can be less reliable, especially for very short phrases and Indian languages. It allows about 5,000 characters per day per internet connection.
- Text-to-speech also needs an internet connection and is not available for every language.
- The text limit per translation is 5,000 characters.
- Translations are machine-generated and should not be used for important documents without checking.

## Possible improvements
- Use the official Google Cloud or Microsoft Translator API with a secret key
- Translate uploaded text files
- Save a history of translations

## Tech
Python, Streamlit, deep-translator, gTTS, requests