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

    def clean_translation_text(self, text: str) -> tuple[str, bool]:
        """Clean translation text by removing notes, comments, and disclaimers.
        Returns (cleaned_text, has_artifacts)"""
        if not text:
            return text, False

        lines = text.split('\n')
        cleaned_lines = []
        has_artifacts = False

        skip_patterns = [
            'note:', 'note that:', 'please note', 'important:',
            'disclaimer', 'warning:', 'caution:', 'however,',
            'however please note', 'but should note', 'ควรสังเกต',
            'there are some', 'appears to be', 'without meaning',
            'similar to typing', 'qwerty', 'keyboard layout',
            'isn\'t a meaningful', 'translation as it\'s',
            'not an actual word', 'not a real word',
            'random letters', 'gibberish', 'nonsense',
            'cannot translate', 'unable to translate',
            'no meaningful translation', 'no translation available',
            'meaningless', 'not meaningful', 'not a word',
            'seems incomplete', 'cut off', 'fragment', 'фрагмент',
            'неполный', 'обрезанный', 'seems to be part',
            'for a more accurate', 'would be helpful', 'для более точного',
            'complete phrase', 'полную фразу',
            # Additional patterns for parentheses artifacts
            'this is a', 'this is an', 'this is the',
            'это ', 'это -', 'это значит',
            'which means', 'which translates',
            'который означает', 'которая означает',
            'translation of', 'перевод',
            'common greeting', 'распространенное приветствие',
            'literally means', 'буквально означает'
        ]

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check if line contains skip patterns
            line_lower = line_stripped.lower()
            should_skip = False

            for pattern in skip_patterns:
                if pattern in line_lower:
                    should_skip = True
                    has_artifacts = True
                    break

            if should_skip:
                continue

            # Skip lines that are just parentheses, brackets, or very short
            if (line_stripped.startswith('(') and line_stripped.endswith(')') and len(line_stripped) < 50) or \
               (line_stripped.startswith('[') and line_stripped.endswith(']') and len(line_stripped) < 50) or \
               len(line_stripped) < 3:
                has_artifacts = True
                continue

            cleaned_lines.append(line)

        # If we filtered everything out, return original text
        if not cleaned_lines:
            return text.strip(), has_artifacts

        return '\n'.join(cleaned_lines).strip(), has_artifacts
    
    def translate_to_english(self, text: str, source_lang: str, model: str) -> Optional[str]:
        """Translate text to English"""
        try:
            if not isinstance(text, str) or not text.strip():
                logger.error(f"Invalid text input: {text}")
                return None

            if source_lang == 'en':
                return text

            prompt = f"Translate to English:\n\n{text}"

            logger.info(f"Translating from {SUPPORTED_LANGUAGES[source_lang]} to English")
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

            # Simple cleaning for individual translation calls
            translated_text, _ = self.clean_translation_text(translated_text)

            if not translated_text:
                logger.error("Got empty translation text after cleaning")
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

            logger.info(f"Translating from English to {SUPPORTED_LANGUAGES[target_lang]}")
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

            # Simple cleaning for individual translation calls
            translated_text, _ = self.clean_translation_text(translated_text)

            if not translated_text:
                logger.error("Got empty translation text after cleaning")
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
            'control_translation': None,
            'has_artifacts': False,
            'full_response': None,
            'json_success': False,
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
            raw_response = self.client.chat.completions.create(
                model=translation_model,
                messages=[
                    {"role": "user", "content": f"Translate to English:\n\n{text}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            if raw_response.choices and raw_response.choices[0].message:
                full_text = raw_response.choices[0].message.content.strip()
                results['full_response'] = full_text
                _, has_artifacts = self.clean_translation_text(full_text)
                results['has_artifacts'] = has_artifacts

                # Try to get clean translation via JSON if artifacts detected
                if has_artifacts:
                    clean_prompt = f"""Translate to English and return ONLY a JSON object with this exact format:
{{
    "translation": "clean translation here",
    "notes": "any additional notes or comments"
}}

Text to translate: {text}"""

                    try:
                        clean_response = self.client.chat.completions.create(
                            model=translation_model,
                            messages=[
                                {"role": "user", "content": clean_prompt}
                            ],
                            temperature=0.1,
                            max_tokens=1000
                        )

                        if clean_response.choices and clean_response.choices[0].message:
                            clean_content = clean_response.choices[0].message.content.strip()

                            try:
                                import json
                                json_data = json.loads(clean_content)
                                if 'translation' in json_data and json_data['translation']:
                                    clean_translation = json_data['translation'].strip()
                                    results['english_translation'] = clean_translation
                                    results['json_success'] = True
                                    results['has_artifacts'] = False  # Reset artifacts flag since we got clean JSON
                                    logger.info(f"Successfully got clean English translation from JSON: {clean_translation}")
                                    logger.debug(f"Full JSON response: {clean_content}")
                                else:
                                    raise ValueError("No translation in JSON")
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"JSON parsing failed for English: {e}")
                                logger.debug(f"Raw content that failed to parse: {clean_content}")
                                results['english_translation'], _ = self.clean_translation_text(full_text)
                                logger.info("JSON parsing failed, using text cleaning for English")
                    except Exception as e:
                        logger.warning(f"Clean JSON request failed: {e}")
                        results['english_translation'], _ = self.clean_translation_text(full_text)
                else:
                    results['english_translation'] = full_text
                    results['json_success'] = True  # No artifacts, so it's clean
                    results['has_artifacts'] = False  # Explicitly set to False

                if not results['english_translation']:
                    results['error'] = "Не удалось перевести на английский"
                    return results
            else:
                results['error'] = "Не удалось получить ответ от API"
                return results
            
            logger.info("Successfully translated to English")
            
            # If target is English, we're done
                        # Step 2: Translate from English to target language
            raw_response_2 = self.client.chat.completions.create(
                model=translation_model,
                messages=[
                    {"role": "user", "content": f"Translate to {SUPPORTED_LANGUAGES[target_lang]}:\n\n{results['english_translation']}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            if raw_response_2.choices and raw_response_2.choices[0].message:
                full_text_2 = raw_response_2.choices[0].message.content.strip()
                _, has_artifacts_2 = self.clean_translation_text(full_text_2)
                results['has_artifacts'] = results['has_artifacts'] or has_artifacts_2

                # Try to get clean translation via JSON if artifacts detected
                if has_artifacts_2:
                    clean_prompt_2 = f"""Translate to {SUPPORTED_LANGUAGES[target_lang]} and return ONLY a JSON object with this exact format:
{{
    "translation": "clean translation here",
    "notes": "any additional notes or comments"
}}

English text to translate: {results['english_translation']}"""

                    try:
                        clean_response_2 = self.client.chat.completions.create(
                            model=translation_model,
                            messages=[
                                {"role": "user", "content": clean_prompt_2}
                            ],
                            temperature=0.1,
                            max_tokens=1000
                        )

                        if clean_response_2.choices and clean_response_2.choices[0].message:
                            clean_content_2 = clean_response_2.choices[0].message.content.strip()

                            try:
                                import json
                                json_data_2 = json.loads(clean_content_2)
                                if 'translation' in json_data_2 and json_data_2['translation']:
                                    clean_translation_2 = json_data_2['translation'].strip()
                                    results['final_translation'] = clean_translation_2
                                    results['json_success'] = True
                                    results['has_artifacts'] = False  # Reset artifacts flag since we got clean JSON
                                    logger.info(f"Successfully got clean final translation from JSON: {clean_translation_2}")
                                    logger.debug(f"Full JSON response: {clean_content_2}")
                                else:
                                    raise ValueError("No translation in JSON")
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"JSON parsing failed for final translation: {e}")
                                logger.debug(f"Raw content that failed to parse: {clean_content_2}")
                                results['final_translation'], _ = self.clean_translation_text(full_text_2)
                                logger.info("JSON parsing failed, using text cleaning for final translation")
                    except Exception as e:
                        logger.warning(f"Clean JSON request failed for final translation: {e}")
                        results['final_translation'], _ = self.clean_translation_text(full_text_2)
                else:
                    results['final_translation'] = full_text_2
                    results['json_success'] = True
                    results['has_artifacts'] = False  # No artifacts, so it's clean

                if not results['final_translation']:
                    results['error'] = f"Не удалось перевести с английского на {SUPPORTED_LANGUAGES[target_lang]}"
                    return results
            else:
                results['error'] = "Не удалось получить ответ от API для финального перевода"
                return results

            # Step 3: Control translation - direct translation back to source language
            if source_lang != target_lang:
                logger.info(f"Performing direct control translation: {SUPPORTED_LANGUAGES[target_lang]} -> {SUPPORTED_LANGUAGES[source_lang]}")

                control_prompt = f"Translate to {SUPPORTED_LANGUAGES[source_lang]}:\n\n{results['final_translation']}"
                response = self.client.chat.completions.create(
                    model=translation_model,
                    messages=[
                        {"role": "user", "content": control_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )

                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    control_text = response.choices[0].message.content.strip()
                    results['control_translation'], _ = self.clean_translation_text(control_text)
                    logger.info("Control translation completed successfully")
                else:
                    results['control_translation'] = None

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
            logger.info(f"Starting speech-to-text with model: {model}")
            logger.info(f"Audio file path: {audio_file_path}")

            # Check if file exists
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None

            # Check file size and format
            file_size = os.path.getsize(audio_file_path)
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            logger.info(f"Audio file size: {file_size} bytes, format: {file_ext}")

            if file_size == 0:
                logger.error("Audio file is empty")
                return None

            # Convert OGG to MP3 if needed
            temp_file = None
            try:
                if file_ext in ['.ogg', '.oga']:
                    import subprocess
                    temp_file = audio_file_path.rsplit('.', 1)[0] + '.mp3'
                    logger.info(f"Converting {file_ext} to MP3: {temp_file}")
                    
                    # Use ffmpeg to convert
                    result = subprocess.run([
                        'ffmpeg', '-i', audio_file_path,
                        '-acodec', 'libmp3lame',
                        '-y',  # Overwrite output file if exists
                        temp_file
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"FFmpeg conversion failed: {result.stderr}")
                        return None
                    
                    audio_file_path = temp_file
                    logger.info("Conversion successful")

                # Supported formats check
                supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
                if os.path.splitext(audio_file_path)[1].lower() not in supported_formats:
                    logger.warning(f"File format {file_ext} might not be supported. Supported formats: {', '.join(supported_formats)}")

                logger.info("Opening audio file and sending to API...")
                with open(audio_file_path, 'rb') as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=model,  # Keep full model name with prefix
                        file=audio_file,
                        response_format="text"
                    )
                
                logger.info("Got response from API")
                logger.debug(f"Raw response type: {type(response)}")

                if isinstance(response, str):
                    result = response.strip()
                    logger.info(f"Successfully transcribed audio to text (length: {len(result)})")
                    logger.debug(f"Transcription result: {result[:100]}..." if len(result) > 100 else f"Transcription result: {result}")
                    return result
                else:
                    result = str(response).strip()
                    logger.warning(f"Unexpected response type: {type(response)}, converting to string")
                    logger.debug(f"Converted result: {result[:100]}..." if len(result) > 100 else f"Converted result: {result}")
                    return result

            finally:
                # Cleanup temporary file if it was created
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temporary file: {e}")
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            return None