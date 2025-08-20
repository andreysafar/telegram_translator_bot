import os

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'YOUR_OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Supported languages
SUPPORTED_LANGUAGES = {
    'ru': 'Russian',
    'th': 'Thai', 
    'en': 'English'
}

# Default models
DEFAULT_TRANSLATION_MODEL = "anthropic/claude-3.5-sonnet"
DEFAULT_STT_MODEL = "openai/whisper-large-v3"

# Available models for user selection
AVAILABLE_TRANSLATION_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.1-70b-instruct"
]

AVAILABLE_STT_MODELS = [
    "openai/whisper-large-v3",
    "openai/whisper-1"
]

# Translation prompts
TRANSLATION_PROMPTS = {
    'to_english': """Translate the following text to English. Provide only the translation without any additional text or explanations:

{text}""",
    
    'from_english': """Translate the following English text to {target_language}. Provide only the translation without any additional text or explanations:

{text}""",
    
    'control_translation': """Translate the following {source_language} text back to {target_language} to verify accuracy. Provide only the translation without any additional text or explanations:

{text}"""
}

