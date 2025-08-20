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
            logger.debug(f"API Response: {response}")
            
            # Extract and validate response
            if not response.choices or not response.choices[0].message:
                raise ValueError("Invalid response format from API")
                
            translated_text = response.choices[0].message.content
            if not translated_text:
                raise ValueError("Empty translation received")
                
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
                english_prompt = TRANSLATION_PROMPTS['to_english']
                results['english_translation'] = self.translate_text(
                    text, translation_model, english_prompt
                )
                
                if not results['english_translation']:
                    results['error'] = "Не удалось перевести на английский"
                    return results
            else:
                results['english_translation'] = text
            
            # Step 2: Translate from English to target language (if target is not English)
            if target_lang != 'en':
                target_lang_name = SUPPORTED_LANGUAGES[target_lang]
                from_english_prompt = TRANSLATION_PROMPTS['from_english'].format(
                    target_language=target_lang_name
                )
                results['final_translation'] = self.translate_text(
                    results['english_translation'], translation_model, from_english_prompt
                )
                
                if not results['final_translation']:
                    results['error'] = "Не удалось перевести с английского"
                    return results
            else:
                results['final_translation'] = results['english_translation']
            
            # Step 3: Control translation (translate back to original language)
            if source_lang != target_lang:
                source_lang_name = SUPPORTED_LANGUAGES[source_lang]
                target_lang_name = SUPPORTED_LANGUAGES[target_lang]
                
                control_prompt = TRANSLATION_PROMPTS['control_translation'].format(
                    source_language=target_lang_name,
                    target_language=source_lang_name
                )
                results['control_translation'] = self.translate_text(
                    results['final_translation'], translation_model, control_prompt
                )
            
            # Validate final results
            if not results['final_translation']:
                raise ValueError("Не получен финальный перевод")
            
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

