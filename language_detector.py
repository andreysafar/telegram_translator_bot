from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from config import SUPPORTED_LANGUAGES

# Set seed for consistent results
DetectorFactory.seed = 0

class LanguageDetector:
    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
    
    def detect_language(self, text: str, user_native_language: str = 'ru') -> str:
        """Detect language of the text with fallback to user's native language"""
        if not text or not text.strip():
            return user_native_language

        # For very short text, try to detect but with more aggressive fallback
        if len(text.strip()) < 3:
            # Check for obvious Cyrillic characters
            cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
            if any(char in cyrillic_chars for char in text):
                return 'ru'

            # Check for Thai characters (basic detection)
            thai_chars = set('กขคงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ')
            if any(char in thai_chars for char in text):
                return 'th'

            # Default to native language
            return user_native_language
        
        try:
            detected = detect(text)
            
            # Map detected language to our supported languages
            if detected in self.supported_languages:
                return detected
            
            # Handle common language variations
            language_mapping = {
                'uk': 'ru',  # Ukrainian -> Russian
                'be': 'ru',  # Belarusian -> Russian
                'bg': 'ru',  # Bulgarian -> Russian (Cyrillic script)
            }
            
            if detected in language_mapping:
                return language_mapping[detected]
            
            # If detected language is not supported, return user's native language
            return user_native_language
            
        except LangDetectException:
            # If detection fails, return user's native language
            return user_native_language
    
    def determine_target_language(self, source_language: str, user_native_language: str = 'ru') -> str:
        """Determine target language based on source language and user preferences"""
        # If source is Russian, translate to Thai
        if source_language == 'ru':
            return 'th'
        
        # If source is Thai or English, translate to Russian
        if source_language in ['th', 'en']:
            return 'ru'
        
        # Default fallback
        return 'ru' if user_native_language != 'ru' else 'th'
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        return self.supported_languages.get(lang_code, lang_code)

