import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Admin user IDs from environment variable
admin_ids_str = os.getenv('BOT_ADMIN_IDS', '')
ADMIN_USER_IDS = [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip().isdigit()]



# Supported languages
SUPPORTED_LANGUAGES = {
    'ru': 'Russian',
    'th': 'Thai', 
    'en': 'English'
}

# Default models
DEFAULT_TRANSLATION_MODEL = "anthropic/claude-3.5-sonnet"
DEFAULT_STT_MODEL = "anthropic/claude-3-opus"  # Supports audio input

# Available models for user selection
AVAILABLE_TRANSLATION_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-oss-120b",
    "google/gemini-flash-1.5-8b",
    "google/gemini-flash-1.5",
    "google/gemini-2.0-flash-001"
]

AVAILABLE_STT_MODELS = [
    "anthropic/claude-3-opus",  # Best audio support
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku"
]

