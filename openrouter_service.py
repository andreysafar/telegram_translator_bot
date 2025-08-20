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
    
    def translate_text(self, text: str, target_language: str, model: str) -> Optional[str]:
        """Translate text to target language using specified model"""
        try:
            # Ensure text is a string
            if not isinstance(text, str) or not text.strip():
                logger.error(f"Invalid text input: {text}")
                return None
            
            # Create simple prompt without placeholders
            prompt = f"Translate the following text to {target_language}. Provide only the translation without any additional text or explanations:\n\n{text}"
            
            # Log request details
            logger.info(f"Making translation request with model: {model}")
            logger.debug(f"Target language: {target_language}")
            logger.debug(f"Text to translate: {text[:100]}..." if len(text) > 100 else f"Text to translate: {text}")
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Log response
            logger.info("Got response from OpenRouter API")
            
            # Extract and validate response
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
            
            logger.info(f"Successfully translated text (length: {len(translated_text)})")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return None
    
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
    
    def perform_translation_chain(self, text: str, source_lang: str, target_lang: str, 
                                translation_model: str) -> Dict[str, str]:
        """
        Perform translation with simplified logic:
        1. Translate directly to target language
        2. Optionally translate back for control
        """
        logger.info(f"Starting translation: {source_lang} -> {target_lang}")
        logger.info(f"Using model: {translation_model}")
        
        results = {
            'original': text,
            'source_language': source_lang,
            'target_language': target_lang,
            'final_translation': None,
            'control_translation': None,
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
            
            # Get language names
            target_lang_name = SUPPORTED_LANGUAGES[target_lang]
            source_lang_name = SUPPORTED_LANGUAGES[source_lang]
            
            # Direct translation to target language
            logger.info(f"Translating to {target_lang_name}")
            results['final_translation'] = self.translate_text(
                text, target_lang_name, translation_model
            )
            
            if not results['final_translation']:
                results['error'] = f"Не удалось перевести на {target_lang_name}"
                return results
            
            logger.info("Successfully translated to target language")
            
            # Optional control translation back to source language
            if source_lang != target_lang:
                logger.info(f"Performing control translation back to {source_lang_name}")
                results['control_translation'] = self.translate_text(
                    results['final_translation'], source_lang_name, translation_model
                )
                
                if results['control_translation']:
                    logger.info("Successfully completed control translation")
                else:
                    logger.warning("Control translation failed, but continuing")
            
            logger.info("Translation chain completed successfully")
            return results
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Translation chain error: {error_msg}")
            results['error'] = f"Ошибка перевода: {error_msg}"
            return results