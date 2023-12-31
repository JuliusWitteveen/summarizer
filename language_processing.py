from langdetect import detect
from translate import Translator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_language(text):
    """
    Detects the language of the given text.

    Args:
        text (str): The text for which to detect the language.

    Returns:
        str: The detected language code (e.g., 'en' for English). Returns 'unknown' if detection fails.

    Notes:
        Uses the 'langdetect' library for language detection.
    """
    try:
        language = detect(text)
        logging.info(f"Detected language: {language}")
        return language
    except Exception as e:
        logging.error(f"Error in language detection: {e}")
        return "unknown"

def translate_prompt(prompt_text, target_language):
    """
    Translates the given prompt text to the specified target language.

    Args:
        prompt_text (str): The text to be translated.
        target_language (str): The target language code (e.g., 'nl' for Dutch).

    Returns:
        str: The translated text. Returns the original text if translation fails or is not supported.

    Notes:
        Currently supports translation to Dutch ('nl') and English ('en') using the 'translate' library.
        Logs a message if the target language is not supported.
    """
    if target_language not in ["nl", "en"]:
        logging.warning(f"Translation not supported for language: {target_language}")
        return prompt_text

    translator = Translator(to_lang=target_language)
    try:
        translated_text = translator.translate(prompt_text)
        logging.info(f"Translated text to {target_language}: {translated_text}")
        return translated_text
    except Exception as e:
        logging.error(f"Error in translating text to {target_language}: {e}")
        return prompt_text
