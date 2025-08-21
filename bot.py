import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

from config import *
from user_storage import UserStorage
from openrouter_service import OpenRouterService
from language_detector import LanguageDetector
from messages import get_message
from tts_service import TTSService

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
        self.tts_service = TTSService()
        
        # Group chat enable list (admin can add/remove groups)
        self.enabled_groups = set()
        
        # Store last translations for playback/edit
        self.last_translations = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Create or get user settings
        user_settings = self.user_storage.get_user(user.id)
        if user.username:
            self.user_storage.update_user(user.id, username=user.username)
        
        # Get user's language
        user_lang = user_settings.get('native_language', 'en')
        
        # Get appropriate message
        welcome_message = get_message('start', user_lang)
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        user_settings = self.user_storage.get_user(user.id)
        user_lang = user_settings.get('native_language', 'en')
        
        help_text = get_message('help', user_lang)
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def lang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lang command to set native language"""
        user = update.effective_user
        user_settings = self.user_storage.get_user(user.id)
        user_lang = user_settings.get('native_language', 'en')
        
        # If language code provided as argument, process it
        if context.args:
            lang_code = context.args[0].lower()
            if lang_code in SUPPORTED_LANGUAGES:
                self.user_storage.set_native_language(user.id, lang_code)
                success_text = get_message('lang_success', lang_code).format(
                    lang_name=SUPPORTED_LANGUAGES[lang_code]
                )
                await update.message.reply_text(success_text, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Create language selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇹🇭 ไทย", callback_data="lang_th"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message in all supported languages
        help_text = "\n\n".join([
            get_message('lang_help', lang).format(
                current_lang=SUPPORTED_LANGUAGES[user_lang]
            ) for lang in ['ru', 'th', 'en']
        ])
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        user = update.effective_user
        user_settings = self.user_storage.get_user(user.id)
        user_lang = user_settings.get('native_language', 'en')
        
        # Get base config message
        if not context.args:
            # Determine if user is admin
            is_admin = user.id in ADMIN_USER_IDS
            
            # Get appropriate section
            admin_section = get_message('config_admin_section' if is_admin else 'config_non_admin_section', user_lang)
            admin_commands = get_message('config_admin_commands', user_lang) if is_admin else ""
            
            # Format config message
            config_text = get_message('config', user_lang).format(
                admin_section=admin_section,
                native_lang=SUPPORTED_LANGUAGES[user_lang],
                translation_model=user_settings['translation_model'].split('/')[-1],
                stt_model=user_settings['stt_model'].split('/')[-1],
                admin_commands=admin_commands
            )
            
            await update.message.reply_text(config_text, parse_mode=ParseMode.MARKDOWN)
            return
            
        # Only admins can proceed past this point
        if user.id not in ADMIN_USER_IDS:
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
                    f"Доступные модели: {', '.join(m.split('/')[-1] for m in AVAILABLE_TRANSLATION_MODELS)}"
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
                    f"Доступные модели: {', '.join(m.split('/')[-1] for m in AVAILABLE_STT_MODELS)}"
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
            
        # Check if this is a reply to edit request
        if update.message.reply_to_message and 'editing_translation' in context.user_data:
            translation_hash = context.user_data['editing_translation']
            translation = self.last_translations.get(translation_hash)
            
            if translation:
                # Show typing indicator
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
                
                # Get user settings
                user_settings = self.user_storage.get_user(user.id)
                
                # Perform new translation with correction prompt
                translation_result = self.openrouter_service.perform_translation_chain(
                    text=translation['original'],
                    source_lang=translation['source_lang'],
                    target_lang=translation['lang'],
                    translation_model=user_settings['translation_model'],
                    correction_prompt=text
                )
                
                if translation_result.get('error'):
                    await update.message.reply_text(
                        f"❌ Ошибка перевода: {translation_result['error']}"
                    )
                    return
                
                try:
                    # Try to delete previous translation message if possible
                    if (update.message.reply_to_message and 
                        update.message.reply_to_message.reply_to_message):
                        await update.message.reply_to_message.reply_to_message.delete()
                except Exception as e:
                    logger.warning(f"Failed to delete previous message: {e}")
                
                # Send new translation
                await self.send_translation_result(update, translation_result)
                
                # Clear editing context
                del context.user_data['editing_translation']
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

        # Show control translation if available
        if result.get('control_translation'):
            message_parts.append("")
            message_parts.append(f"✅ {result['control_translation']}")

        
        formatted_message = "\n".join(message_parts)

        # Store translation for playback/edit
        translation_hash = hash(result['original'])
        self.last_translations[translation_hash] = {
            'text': result['final_translation'],
            'lang': target_lang,
            'original': result['original'],
            'source_lang': source_lang
        }

        # Create keyboard with action buttons
        keyboard_buttons = [
            [
                InlineKeyboardButton("🎵", callback_data=f"play_{translation_hash}"),
                InlineKeyboardButton("✏️", callback_data=f"edit_{translation_hash}")
            ]
        ]
        
        # Add show_full button if needed
        if result.get('has_artifacts') and result.get('json_success'):
            keyboard_buttons.append([
                InlineKeyboardButton("📋 Показать полный ответ с примечаниями", callback_data=f"show_full_{translation_hash}")
            ])

        keyboard = InlineKeyboardMarkup(keyboard_buttons)

        await update.message.reply_text(
            formatted_message,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id,
            reply_markup=keyboard
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback buttons"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        data = query.data
        
        if data.startswith('lang_'):
            # Handle language selection
            lang_code = data.split('_')[1]
            if lang_code in SUPPORTED_LANGUAGES:
                user = update.effective_user
                self.user_storage.set_native_language(user.id, lang_code)
                
                # Send confirmation in the new language
                success_text = get_message('lang_success', lang_code).format(
                    lang_name=SUPPORTED_LANGUAGES[lang_code]
                )
                await query.message.edit_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            return
            
        elif data.startswith('show_full_'):
            # Handle show_full button
            await query.edit_message_text(
                "📋 **Полный ответ API с примечаниями**\n\n"
                "⚠️ В этой версии показ полного ответа отключен.\n\n"
                "Оригинальный ответ API содержал:\n"
                "• Чистый перевод (который показан выше)\n"
                "• Дополнительные примечания и комментарии\n"
                "• Техническую информацию от модели\n\n"
                "Это было автоматически скрыто для чистоты вывода.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data.startswith('play_'):
            # Handle play button
            translation_hash = int(data.split('_')[1])
            translation = self.last_translations.get(translation_hash)
            
            if not translation:
                await query.message.reply_text("❌ Перевод не найден")
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="record_voice"
            )
            
            # Convert text to speech
            audio_path = self.tts_service.text_to_speech(
                translation['text'],
                translation['lang']
            )
            
            if not audio_path:
                await query.message.reply_text("❌ Не удалось создать аудио")
                return
            
            # Send voice message
            try:
                with open(audio_path, 'rb') as audio:
                    await context.bot.send_voice(
                        chat_id=update.effective_chat.id,
                        voice=audio,
                        reply_to_message_id=query.message.message_id
                    )
            finally:
                # Clean up audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
        
        elif data.startswith('edit_'):
            # Handle edit button
            translation_hash = int(data.split('_')[1])
            translation = self.last_translations.get(translation_hash)
            
            if not translation:
                await query.message.reply_text("❌ Перевод не найден")
                return
            
            # Get user's language for prompts
            user_settings = self.user_storage.get_user(update.effective_user.id)
            user_lang = user_settings.get('native_language', 'en')
            
            # Ask for correction
            await query.message.reply_text(
                get_message('edit_prompt', user_lang),
                reply_markup=ForceReply(selective=True)
            )
            
            # Store context for the next message
            context.user_data['editing_translation'] = translation_hash

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

        # Callback handler for all buttons
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))

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
        
        # Initialize TTS models
        logger.info("Initializing TTS models...")
        if not self.tts_service.initialize_models():
            logger.error("Failed to initialize TTS models. Voice playback will be unavailable.")
        
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