from langdetect import detect
from translate import Translator
import logging

def detect_language(text):
    """
    Detect the language of the given text.
    """
    try:
        return detect(text)
    except Exception as e:
        logging.error(f"Error in language detection: {e}")
        return "unknown"

def translate_prompt(prompt_text, target_language):
    """
    Translate the prompt text to the target language.
    """
    if target_language not in ["nl", "en"]:
        # Currently supports Dutch and English. Add more as needed.
        logging.info(f"Translation not supported for language: {target_language}")
        return prompt_text

    translator = Translator(to_lang=target_language)
    try:
        return translator.translate(prompt_text)
    except Exception as e:
        logging.error(f"Error in translating text: {e}")
        return prompt_text
