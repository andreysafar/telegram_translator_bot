import openai
import os
import logging
from typing import Optional, Dict
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, SUPPORTED_LANGUAGES

# Configure logging
logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/andreysafar/telegram_translator_bot",
                "X-Title": "Telegram Translator Bot"
            }
        )
    
    def translate_to_english(self, text: str, source_lang: str, model: str) -> Optional[str]:
        """Translate text to English"""
        try:
            if not isinstance(text, str) or not text.strip():
                logger.error(f"Invalid text input: {text}")
                return None
            
            if source_lang == 'en':
                return text
            
            prompt = f"Translate to English:\n\n{text}"
            
            logger.info(f"Translating from {source_lang_name} to English")
            logger.debug(f"Text to translate: {text[:100]}..." if len(text) > 100 else f"Text to translate: {text}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            logger.info("Got response from OpenRouter API")
            
            if not response or not response.choices:
                logger.error("Invalid response: no choices")
                return None
                
            if not response.choices[0].message or not response.choices[0].message.content:
                logger.error("Invalid response: no content")
                return None
                
            translated_text = response.choices[0].message.content.strip()
            
            if not translated_text:
                logger.error("Got empty translation text")
                return None
            
            logger.info(f"Successfully translated to English (length: {len(translated_text)})")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation to English error: {str(e)}")
            return None
    
    def translate_from_english(self, text: str, target_lang: str, model: str) -> Optional[str]:
        """Translate English text to target language"""
        try:
            if not isinstance(text, str) or not text.strip():
                logger.error(f"Invalid text input: {text}")
                return None
            
            if target_lang == 'en':
                return text
            
            prompt = f"Translate to {SUPPORTED_LANGUAGES[target_lang]}:\n\n{text}"
            
            logger.info(f"Translating from English to {target_lang_name}")
            logger.debug(f"Text to translate: {text[:100]}..." if len(text) > 100 else f"Text to translate: {text}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            logger.info("Got response from OpenRouter API")
            
            if not response or not response.choices:
                logger.error("Invalid response: no choices")
                return None
                
            if not response.choices[0].message or not response.choices[0].message.content:
                logger.error("Invalid response: no content")
                return None
                
            translated_text = response.choices[0].message.content.strip()
            
            if not translated_text:
                logger.error("Got empty translation text")
                return None
            
            logger.info(f"Successfully translated from English (length: {len(translated_text)})")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation from English error: {str(e)}")
            return None
    
    def perform_translation_chain(self, text: str, source_lang: str, target_lang: str, 
                                translation_model: str) -> Dict[str, str]:
        """
        Perform two-step translation:
        1. Source language -> English
        2. English -> Target language
        """
        logger.info(f"Starting translation chain: {source_lang} -> {target_lang}")
        logger.info(f"Using model: {translation_model}")
        
        results = {
            'original': text,
            'source_language': source_lang,
            'target_language': target_lang,
            'english_translation': None,
            'final_translation': None,
            'error': None
        }
        
        try:
            # Validate input
            if not text or not isinstance(text, str):
                results['error'] = "Некорректный текст для перевода"
                return results
                
            if source_lang not in SUPPORTED_LANGUAGES:
                results['error'] = f"Неподдерживаемый язык: {source_lang}"
                return results
                
            if target_lang not in SUPPORTED_LANGUAGES:
                results['error'] = f"Неподдерживаемый язык: {target_lang}"
                return results
            
            # Step 1: Translate to English
            results['english_translation'] = self.translate_to_english(
                text, source_lang, translation_model
            )
            
            if not results['english_translation']:
                results['error'] = "Не удалось перевести на английский"
                return results
            
            logger.info("Successfully translated to English")
            
            # If target is English, we're done
            if target_lang == 'en':
                results['final_translation'] = results['english_translation']
                return results
            
            # Step 2: Translate from English to target language
            results['final_translation'] = self.translate_from_english(
                results['english_translation'], target_lang, translation_model
            )
            
            if not results['final_translation']:
                results['error'] = f"Не удалось перевести с английского на {SUPPORTED_LANGUAGES[target_lang]}"
                return results
            
            logger.info("Translation chain completed successfully")
            return results
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Translation chain error: {error_msg}")
            results['error'] = f"Ошибка перевода: {error_msg}"
            return results
    
    def speech_to_text(self, audio_file_path: str, model: str) -> Optional[str]:
        """Convert speech to text using Whisper model"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    response_format="text"
                )
            
            if isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return None