import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
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
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Create or get user settings
        user_settings = self.user_storage.get_user(user.id)
        if user.username:
            self.user_storage.update_user(user.id, username=user.username)
        
        welcome_message = f"""
🤖 Привет, {user.first_name}!

Я бот-переводчик для групповых чатов. Поддерживаю переводы между:
🇷🇺 Русским
🇹🇭 Тайским  
🇬🇧 Английским

**Как я работаю:**
1. Получаю сообщение и определяю язык
2. Перевожу на английский
3. Перевожу на целевой язык
4. Делаю контрольный перевод обратно

**Поддерживаю:**
📝 Текстовые сообщения
🎤 Голосовые сообщения

**Команды:**
/config - настройки модели и языка
/help - справка

Добавьте меня в групповой чат и я буду переводить все сообщения!
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
• Трехэтапный процесс перевода с контролем качества

**Команды:**
/start - приветствие и информация о боте
/config - настройки модели перевода и языка
/help - эта справка

**Как работает перевод:**
1. 📥 Получаю ваше сообщение
2. 🔍 Определяю язык (русский/тайский/английский)
3. 🔄 Перевожу через английский на целевой язык
4. ✅ Делаю контрольный перевод для проверки
5. 📤 Отправляю результат с тремя вариантами

**Для голосовых сообщений:**
1. 🎤 Преобразую речь в текст
2. 📝 Показываю распознанный текст
3. 🔄 Применяю стандартный процесс перевода

Просто добавьте меня в групповой чат и начните общаться!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        user = update.effective_user
        user_settings = self.user_storage.get_user(user.id)
        
        keyboard = [
            [InlineKeyboardButton("🌍 Язык носителя", callback_data="config_language")],
            [InlineKeyboardButton("🤖 Модель перевода", callback_data="config_translation_model")],
            [InlineKeyboardButton("🎤 Модель распознавания речи", callback_data="config_stt_model")],
            [InlineKeyboardButton("📊 Текущие настройки", callback_data="config_show")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ **Настройки бота**\n\nВыберите что хотите настроить:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_config_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle config callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_settings = self.user_storage.get_user(user_id)
        
        if query.data == "config_language":
            keyboard = []
            for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
                emoji = "✅" if user_settings['native_language'] == lang_code else ""
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {lang_name}", 
                    callback_data=f"set_language_{lang_code}"
                )])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="config_back")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🌍 **Выберите ваш родной язык:**\n\nЭто поможет точнее определять направление перевода.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "config_translation_model":
            keyboard = []
            for model in AVAILABLE_TRANSLATION_MODELS:
                emoji = "✅" if user_settings['translation_model'] == model else ""
                model_name = model.split('/')[-1]  # Get model name without provider
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {model_name}", 
                    callback_data=f"set_trans_model_{model.replace('/', '_')}"
                )])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="config_back")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🤖 **Выберите модель для перевода:**",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "config_stt_model":
            keyboard = []
            for model in AVAILABLE_STT_MODELS:
                emoji = "✅" if user_settings['stt_model'] == model else ""
                model_name = model.split('/')[-1]
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {model_name}", 
                    callback_data=f"set_stt_model_{model.replace('/', '_')}"
                )])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="config_back")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🎤 **Выберите модель для распознавания речи:**",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "config_show":
            settings_text = f"""
📊 **Ваши текущие настройки:**

🌍 **Родной язык:** {SUPPORTED_LANGUAGES[user_settings['native_language']]}
🤖 **Модель перевода:** {user_settings['translation_model'].split('/')[-1]}
🎤 **Модель распознавания:** {user_settings['stt_model'].split('/')[-1]}
            """
            
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="config_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                settings_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "config_back":
            await self.config_command(update, context)
        
        elif query.data.startswith("set_language_"):
            lang_code = query.data.replace("set_language_", "")
            self.user_storage.set_native_language(user_id, lang_code)
            
            await query.edit_message_text(
                f"✅ Родной язык установлен: {SUPPORTED_LANGUAGES[lang_code]}",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data.startswith("set_trans_model_"):
            model = query.data.replace("set_trans_model_", "").replace("_", "/")
            self.user_storage.set_translation_model(user_id, model)
            
            await query.edit_message_text(
                f"✅ Модель перевода установлена: {model.split('/')[-1]}",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data.startswith("set_stt_model_"):
            model = query.data.replace("set_stt_model_", "").replace("_", "/")
            self.user_storage.set_stt_model(user_id, model)
            
            await query.edit_message_text(
                f"✅ Модель распознавания установлена: {model.split('/')[-1]}",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        if not update.message or not update.message.text:
            return
        
        user = update.effective_user
        text = update.message.text
        
        # Skip if message is a command
        if text.startswith('/'):
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
        
        user = update.effective_user
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
        source_lang_name = self.language_detector.get_language_name(result['source_language'])
        target_lang_name = self.language_detector.get_language_name(result['target_language'])
        
        # Create formatted message
        message_parts = [
            f"🔄 **Перевод** ({source_lang_name} → {target_lang_name})",
            "",
            f"📝 **Оригинал ({source_lang_name}):**",
            f"_{result['original']}_",
            ""
        ]
        
        if result['english_translation'] and result['source_language'] != 'en':
            message_parts.extend([
                f"🇬🇧 **Английский:**",
                f"_{result['english_translation']}_",
                ""
            ])
        
        message_parts.extend([
            f"🎯 **Перевод ({target_lang_name}):**",
            f"**{result['final_translation']}**",
            ""
        ])
        
        if result['control_translation']:
            message_parts.extend([
                f"✅ **Контроль ({source_lang_name}):**",
                f"_{result['control_translation']}_"
            ])
        
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
        application.add_handler(CommandHandler("config", self.config_command))
        
        # Callback query handler for config
        application.add_handler(CallbackQueryHandler(self.handle_config_callback))
        
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

