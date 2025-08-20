import openai
import os
from typing import Optional, Dict
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, TRANSLATION_PROMPTS, SUPPORTED_LANGUAGES

class OpenRouterService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
    
    def translate_text(self, text: str, model: str, prompt: str) -> Optional[str]:
        """Translate text using specified model and prompt"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt.format(text=text)}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Translation error: {e}")
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
            # Step 1: Translate to English (if not already English)
            if source_lang != 'en':
                english_prompt = TRANSLATION_PROMPTS['to_english']
                results['english_translation'] = self.translate_text(
                    text, translation_model, english_prompt
                )
                
                if not results['english_translation']:
                    results['error'] = "Failed to translate to English"
                    return results
            else:
                results['english_translation'] = text
            
            # Step 2: Translate from English to target language (if target is not English)
            if target_lang != 'en':
                target_lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
                from_english_prompt = TRANSLATION_PROMPTS['from_english'].format(
                    target_language=target_lang_name
                )
                results['final_translation'] = self.translate_text(
                    results['english_translation'], translation_model, from_english_prompt
                )
                
                if not results['final_translation']:
                    results['error'] = "Failed to translate from English"
                    return results
            else:
                results['final_translation'] = results['english_translation']
            
            # Step 3: Control translation (translate back to original language)
            if source_lang != target_lang:
                source_lang_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
                target_lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
                
                control_prompt = TRANSLATION_PROMPTS['control_translation'].format(
                    source_language=target_lang_name,
                    target_language=source_lang_name
                )
                results['control_translation'] = self.translate_text(
                    results['final_translation'], translation_model, control_prompt
                )
            
            return results
            
        except Exception as e:
            results['error'] = f"Translation chain error: {e}"
            return results

