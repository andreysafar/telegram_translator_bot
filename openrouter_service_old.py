import openai
import os
import logging
from typing import Optional, Dict
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, TRANSLATION_PROMPTS, SUPPORTED_LANGUAGES

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
    
    def translate_text(self, text: str, model: str, prompt: str) -> Optional[str]:
        """Translate text using specified model and prompt"""
        try:
            # Ensure text is a string
            if not isinstance(text, str):
                raise ValueError(f"Text must be a string, got {type(text)}")
            
            # Format prompt with text
            formatted_prompt = prompt.format(text=text)
            
            # Log request details
            logger.info(f"Making translation request with model: {model}")
            logger.debug(f"Prompt: {formatted_prompt}")
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Log response
            logger.info("Got response from OpenRouter API")
            logger.debug(f"Full API Response: {response}")
            
            # Extract and validate response
            if not hasattr(response, 'choices'):
                logger.error("Response has no 'choices' attribute")
                raise ValueError("Invalid response format: no choices")
                
            if not response.choices:
                logger.error("Response choices is empty")
                raise ValueError("Invalid response format: empty choices")
                
            if not hasattr(response.choices[0], 'message'):
                logger.error("First choice has no 'message' attribute")
                logger.debug(f"First choice content: {response.choices[0]}")
                raise ValueError("Invalid response format: no message")
                
            if not hasattr(response.choices[0].message, 'content'):
                logger.error("Message has no 'content' attribute")
                logger.debug(f"Message content: {response.choices[0].message}")
                raise ValueError("Invalid response format: no content")
                
            translated_text = response.choices[0].message.content
            
            if not translated_text:
                logger.error("Got empty translation text")
                raise ValueError("Empty translation received")
            
            logger.info(f"Successfully translated text (length: {len(translated_text)})")
            return translated_text.strip()
            
        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            logger.error(error_msg)
            if "401" in str(e):
                error_msg = "Ошибка авторизации OpenRouter API. Проверьте API ключ."
            elif "text" in str(e):
                error_msg = "Ошибка формата текста. Убедитесь, что текст корректен."
            elif "choices" in str(e):
                error_msg = "Некорректный ответ от API. Попробуйте еще раз."
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
            
            return response.strip()
            
        except Exception as e:
            print(f"Speech-to-text error: {e}")
            return None
    
    def perform_translation_chain(self, text: str, source_lang: str, target_lang: str, 
                                translation_model: str) -> Dict[str, str]:
        """
        Perform the complete translation chain:
        1. Original -> English
        2. English -> Target language
        3. Target language -> Original (control)
        """
        logger.info(f"Starting translation chain: {source_lang} -> {target_lang}")
        logger.info(f"Using model: {translation_model}")
        logger.debug(f"Input text: {text[:100]}..." if len(text) > 100 else f"Input text: {text}")
        results = {
            'original': text,
            'source_language': source_lang,
            'target_language': target_lang,
            'english_translation': None,
            'final_translation': None,
            'control_translation': None,
            'error': None
        }
        
        try:
            # Validate input
            if not text or not isinstance(text, str):
                raise ValueError("Invalid input text")
            if not source_lang in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported source language: {source_lang}")
            if not target_lang in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported target language: {target_lang}")
            
            # Step 1: Translate to English (if not already English)
            if source_lang != 'en':
                logger.info("Step 1: Translating to English")
                english_prompt = TRANSLATION_PROMPTS['to_english']
                results['english_translation'] = self.translate_text(
                    text, translation_model, english_prompt
                )
                
                if not results['english_translation']:
                    logger.error("Failed to translate to English")
                    results['error'] = "Не удалось перевести на английский"
                    return results
                logger.info("Successfully translated to English")
            else:
                logger.info("Source is English, skipping first translation")
                results['english_translation'] = text
            
            # Step 2: Translate from English to target language (if target is not English)
            if target_lang != 'en':
                logger.info("Step 2: Translating from English to target language")
                target_lang_name = SUPPORTED_LANGUAGES[target_lang]
                from_english_prompt = TRANSLATION_PROMPTS['from_english'].format(
                    target_language=target_lang_name
                )
                logger.debug(f"Using prompt template: {from_english_prompt}")
                
                results['final_translation'] = self.translate_text(
                    results['english_translation'], translation_model, from_english_prompt
                )
                
                if not results['final_translation']:
                    logger.error("Failed to translate from English to target language")
                    results['error'] = "Не удалось перевести с английского"
                    return results
                logger.info("Successfully translated to target language")
            else:
                logger.info("Target is English, using English translation as final")
                results['final_translation'] = results['english_translation']
            
            # Step 3: Control translation (translate back to original language)
            if source_lang != target_lang:
                logger.info("Step 3: Performing control translation back to source language")
                source_lang_name = SUPPORTED_LANGUAGES[source_lang]
                target_lang_name = SUPPORTED_LANGUAGES[target_lang]
                
                control_prompt = TRANSLATION_PROMPTS['control_translation'].format(
                    source_language=target_lang_name,
                    target_language=source_lang_name
                )
                logger.debug(f"Using control prompt template: {control_prompt}")
                
                results['control_translation'] = self.translate_text(
                    results['final_translation'], translation_model, control_prompt
                )
                
                if results['control_translation']:
                    logger.info("Successfully completed control translation")
                else:
                    logger.warning("Control translation failed, but continuing as it's optional")
            else:
                logger.info("Source and target languages are the same, skipping control translation")
            
            # Validate final results
            if not results['final_translation']:
                logger.error("Final translation is missing")
                raise ValueError("Не получен финальный перевод")
            
            logger.info("Translation chain completed successfully")
            return results
            
        except Exception as e:
            error_msg = str(e)
            if "Invalid input text" in error_msg:
                results['error'] = "Некорректный текст для перевода"
            elif "Unsupported" in error_msg:
                results['error'] = "Неподдерживаемый язык перевода"
            else:
                results['error'] = f"Ошибка перевода: {error_msg}"
            return results

