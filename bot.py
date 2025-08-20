import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, filters
)
from telegram.constants import ParseMode

from config import *
from user_storage import UserStorage
from openrouter_service import OpenRouterService
from language_detector import LanguageDetector

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramTranslatorBot:
    def __init__(self):
        self.user_storage = UserStorage()
        self.openrouter_service = OpenRouterService()
        self.language_detector = LanguageDetector()
        
        # Group chat enable list (admin can add/remove groups)
        self.enabled_groups = set()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Create or get user settings
        user_settings = self.user_storage.get_user(user.id)
        if user.username:
            self.user_storage.update_user(user.id, username=user.username)
        
        if chat.type == 'private':
            welcome_message = f"""
🤖 Привет, {user.first_name}!

Я бот-переводчик для групповых чатов. Поддерживаю переводы между:
🇷🇺 Русским
🇹🇭 Тайским  
🇬🇧 Английским

**Как я работаю:**
1. Получаю сообщение и определяю язык
2. Перевожу через OpenRouter API
3. Отправляю результат

**Команды:**
/lang <ru|th|en> - установить родной язык
/help - справка

**Для администраторов бота:**
/config - настройки бота (только для админов бота)
/enable - включить бота в группе (только для админов бота)
/disable - выключить бота в группе (только для админов бота)

Добавьте меня в групповой чат и я буду переводить все сообщения!
            """
        else:
            welcome_message = f"""
🤖 Бот-переводчик запущен в группе!

Для работы бота администратор бота должен выполнить команду /enable
            """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Справка по боту-переводчику**

**Основные функции:**
• Автоматический перевод сообщений в групповых чатах
• Поддержка русского, тайского и английского языков
• Обработка голосовых сообщений

**Команды для пользователей:**
/start - информация о боте
/lang <ru|th|en> - установить родной язык
/help - эта справка

**Команды для администраторов бота:**
/config - настройки модели (только админы бота)
/enable - включить бота в группе (только админы бота)
/disable - выключить бота в группе (только админы бота)

**Как работает перевод:**
1. 📥 Получаю ваше сообщение
2. 🔍 Определяю язык (русский/тайский/английский)
3. 🔄 Перевожу через OpenRouter API
4. 📤 Отправляю результат

Просто добавьте меня в групповой чат и включите командой /enable!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def lang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lang command to set native language"""
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text(
                "Использование: /lang <ru|th|en>\n\n"
                "Примеры:\n"
                "/lang ru - русский\n"
                "/lang th - тайский\n"
                "/lang en - английский"
            )
            return
        
        lang_code = context.args[0].lower()
        if lang_code not in SUPPORTED_LANGUAGES:
            await update.message.reply_text(
                f"❌ Неподдерживаемый язык: {lang_code}\n"
                "Доступные языки: ru, th, en"
            )
            return
        
        self.user_storage.set_native_language(user.id, lang_code)
        lang_name = SUPPORTED_LANGUAGES[lang_code]
        
        await update.message.reply_text(
            f"✅ Родной язык установлен: {lang_name}"
        )
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command - admin only"""
        user = update.effective_user
        
        # Check if user is bot admin
        if user.id not in ADMIN_USER_IDS:
            await update.message.reply_text(
                "❌ Команда /config доступна только администраторам бота"
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "⚙️ **Настройки бота (только для администраторов)**\n\n"
                "Команды:\n"
                "/config model <model_name> - установить модель перевода\n"
                "/config stt <model_name> - установить модель распознавания речи\n"
                "/config show - показать текущие настройки\n\n"
                "Доступные модели перевода:\n"
                "• claude-3.5-sonnet\n"
                "• gpt-4o\n"
                "• gpt-4o-mini\n"
                "• gemini-pro-1.5\n"
                "• llama-3.1-70b-instruct\n\n"
                "Доступные модели STT:\n"
                "• whisper-large-v3\n"
                "• whisper-1",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        action = context.args[0].lower()
        
        if action == "show":
            # Show current settings for the group/user
            settings = self.user_storage.get_user(user.id)
            await update.message.reply_text(
                f"📊 **Текущие настройки:**\n\n"
                f"🤖 Модель перевода: {settings['translation_model'].split('/')[-1]}\n"
                f"🎤 Модель STT: {settings['stt_model'].split('/')[-1]}",
                parse_mode=ParseMode.MARKDOWN
            )
        elif action == "model" and len(context.args) > 1:
            model_name = context.args[1]
            full_model = None
            
            # Find full model name
            for model in AVAILABLE_TRANSLATION_MODELS:
                if model.endswith(model_name) or model_name in model:
                    full_model = model
                    break
            
            if not full_model:
                await update.message.reply_text(
                    f"❌ Модель '{model_name}' не найдена.\n"
                    "Доступные модели: claude-3.5-sonnet, gpt-4o, gpt-4o-mini, gemini-pro-1.5, llama-3.1-70b-instruct"
                )
                return
            
            self.user_storage.set_translation_model(user.id, full_model)
            await update.message.reply_text(
                f"✅ Модель перевода установлена: {full_model.split('/')[-1]}"
            )
        elif action == "stt" and len(context.args) > 1:
            model_name = context.args[1]
            full_model = None
            
            # Find full model name
            for model in AVAILABLE_STT_MODELS:
                if model.endswith(model_name) or model_name in model:
                    full_model = model
                    break
            
            if not full_model:
                await update.message.reply_text(
                    f"❌ Модель STT '{model_name}' не найдена.\n"
                    "Доступные модели: whisper-large-v3, whisper-1"
                )
                return
            
            self.user_storage.set_stt_model(user.id, full_model)
            await update.message.reply_text(
                f"✅ Модель STT установлена: {full_model.split('/')[-1]}"
            )
        else:
            await update.message.reply_text(
                "❌ Неверная команда. Используйте /config для справки."
            )
    
    async def enable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable bot in group - admin only"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user is bot admin
        if user.id not in ADMIN_USER_IDS:
            await update.message.reply_text(
                "❌ Команда /enable доступна только администраторам бота"
            )
            return
        
        if chat.type == 'private':
            await update.message.reply_text(
                "❌ Команда /enable работает только в групповых чатах"
            )
            return
        
        self.enabled_groups.add(chat.id)
        await update.message.reply_text(
            "✅ Бот включен в этой группе! Теперь я буду переводить сообщения."
        )
    
    async def disable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable bot in group - admin only"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user is bot admin
        if user.id not in ADMIN_USER_IDS:
            await update.message.reply_text(
                "❌ Команда /disable доступна только администраторам бота"
            )
            return
        
        if chat.type == 'private':
            await update.message.reply_text(
                "❌ Команда /disable работает только в групповых чатах"
            )
            return
        
        self.enabled_groups.discard(chat.id)
        await update.message.reply_text(
            "✅ Бот выключен в этой группе. Я больше не буду переводить сообщения."
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        if not update.message or not update.message.text:
            return
        
        chat = update.effective_chat
        user = update.effective_user
        text = update.message.text
        
        # Skip if message is a command
        if text.startswith('/'):
            return
        
        # For group chats, check if bot is enabled
        if chat.type != 'private' and chat.id not in self.enabled_groups:
            return
        
        # Get user settings
        user_settings = self.user_storage.get_user(user.id)
        
        # Detect language
        source_language = self.language_detector.detect_language(
            text, user_settings['native_language']
        )
        
        # Determine target language
        target_language = self.language_detector.determine_target_language(
            source_language, user_settings['native_language']
        )
        
        # Skip translation if source and target are the same
        if source_language == target_language:
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Perform translation
        translation_result = self.openrouter_service.perform_translation_chain(
            text=text,
            source_lang=source_language,
            target_lang=target_language,
            translation_model=user_settings['translation_model']
        )
        
        if translation_result.get('error'):
            await update.message.reply_text(
                f"❌ Ошибка перевода: {translation_result['error']}"
            )
            return
        
        # Format and send translation result
        await self.send_translation_result(update, translation_result)
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages"""
        if not update.message or not update.message.voice:
            return
        
        chat = update.effective_chat
        user = update.effective_user
        
        # For group chats, check if bot is enabled
        if chat.type != 'private' and chat.id not in self.enabled_groups:
            return
        
        user_settings = self.user_storage.get_user(user.id)
        
        try:
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            # Download voice file
            voice_file = await update.message.voice.get_file()
            voice_path = f"voice_{user.id}_{update.message.message_id}.ogg"
            await voice_file.download_to_drive(voice_path)
            
            # Convert to text
            recognized_text = self.openrouter_service.speech_to_text(
                voice_path, user_settings['stt_model']
            )
            
            # Clean up file
            if os.path.exists(voice_path):
                os.remove(voice_path)
            
            if not recognized_text:
                await update.message.reply_text("❌ Не удалось распознать речь")
                return
            
            # Send recognized text
            await update.message.reply_text(
                f"🎤 **Распознанный текст:**\n_{recognized_text}_",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Detect language and translate
            source_language = self.language_detector.detect_language(
                recognized_text, user_settings['native_language']
            )
            
            target_language = self.language_detector.determine_target_language(
                source_language, user_settings['native_language']
            )
            
            if source_language == target_language:
                return
            
            # Perform translation
            translation_result = self.openrouter_service.perform_translation_chain(
                text=recognized_text,
                source_lang=source_language,
                target_lang=target_language,
                translation_model=user_settings['translation_model']
            )
            
            if translation_result.get('error'):
                await update.message.reply_text(
                    f"❌ Ошибка перевода: {translation_result['error']}"
                )
                return
            
            # Format and send translation result
            await self.send_translation_result(update, translation_result)
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            await update.message.reply_text("❌ Ошибка обработки голосового сообщения")
    
    async def send_translation_result(self, update: Update, result: dict):
        """Format and send translation result"""
        # Language flags
        FLAGS = {
            'ru': '🇷🇺',
            'en': '🇬🇧',
            'th': '🇹🇭'
        }
        
        source_lang = result['source_language']
        target_lang = result['target_language']
        
        # Build message parts
        message_parts = []
        
        # Always show English translation
        if source_lang == 'en':
            message_parts.append(f"🇬🇧 {result['original']}")
        elif target_lang == 'en':
            message_parts.append(f"🇬🇧 {result['final_translation']}")
        else:
            message_parts.append(f"🇬🇧 {result['english_translation']}")
        
        # Show target language translation (if not English)
        if target_lang != 'en':
            message_parts.append(f"{FLAGS[target_lang]} {result['final_translation']}")
        
        # Add empty line before original text
        message_parts.append("")
        
        # Show original text with flag
        message_parts.append(f"{FLAGS[source_lang]} {result['original']}")
        
        formatted_message = "\n".join(message_parts)
        
        await update.message.reply_text(
            formatted_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=update.message.message_id
        )
    
    def create_application(self) -> Application:
        """Create and configure the Telegram application"""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("lang", self.lang_command))
        application.add_handler(CommandHandler("config", self.config_command))
        application.add_handler(CommandHandler("enable", self.enable_command))
        application.add_handler(CommandHandler("disable", self.disable_command))
        
        # Text message handler (excluding commands)
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )
        
        # Voice message handler
        application.add_handler(
            MessageHandler(filters.VOICE, self.handle_voice_message)
        )
        
        return application
    
    async def run(self):
        """Run the bot"""
        application = self.create_application()
        
        logger.info("Starting Telegram Translator Bot...")
        
        # Start the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

# Function to run the bot
async def main():
    bot = TelegramTranslatorBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())