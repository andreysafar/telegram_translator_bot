"""
Multilingual messages for the Telegram Translator Bot.
Each message is available in Russian, Thai, and English.
"""

from typing import Dict, Optional
from config import SUPPORTED_LANGUAGES

def get_message(message_id: str, lang: str = 'en') -> str:
    """Get a message in the specified language"""
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
    return MESSAGES.get(message_id, {}).get(lang, MESSAGES[message_id]['en'])

# Message templates for different languages
MESSAGES: Dict[str, Dict[str, str]] = {
    'start': {
        'ru': """
🤖 **Привет! Я бот-переводчик!**

Я помогаю людям общаться на разных языках. Вот что я умею:

• Перевожу текст между русским 🇷🇺, тайским 🇹🇭 и английским 🇬🇧
• Распознаю и перевожу голосовые сообщения 🎤
• Работаю в личных чатах и группах 👥

Используйте /help для подробной информации о командах.

🌐 **Выбор языка интерфейса:**
Сейчас я говорю на русском. Чтобы изменить язык, используйте команду /lang:
• 🇷🇺 Русский (текущий)
• 🇹🇭 ไทย (Thai)
• 🇬🇧 English

Приятного общения! 😊
""",
        'th': """
🤖 **สวัสดี! ฉันคือบอทแปลภาษา!**

ฉันช่วยให้ผู้คนสื่อสารในภาษาต่างๆ ได้ ความสามารถของฉัน:

• แปลระหว่างภาษารัสเซีย 🇷🇺 ไทย 🇹🇭 และอังกฤษ 🇬🇧
• รับรู้และแปลข้อความเสียง 🎤
• ทำงานในแชทส่วนตัวและกลุ่ม 👥

ใช้ /help สำหรับข้อมูลเพิ่มเติมเกี่ยวกับคำสั่ง

🌐 **เลือกภาษาที่ใช้แสดงผล:**
ตอนนี้ฉันพูดภาษาไทย ใช้คำสั่ง /lang เพื่อเปลี่ยนภาษา:
• 🇷🇺 Русский (Russian)
• 🇹🇭 ไทย (ปัจจุบัน)
• 🇬🇧 English

ขอให้สนุกกับการสนทนา! 😊
""",
        'en': """
🤖 **Hello! I'm a Translator Bot!**

I help people communicate in different languages. Here's what I can do:

• Translate between Russian 🇷🇺, Thai 🇹🇭, and English 🇬🇧
• Recognize and translate voice messages 🎤
• Work in private chats and groups 👥

Use /help for detailed information about commands.

🌐 **Interface Language Selection:**
I'm currently speaking English. Use /lang command to change language:
• 🇷🇺 Русский (Russian)
• 🇹🇭 ไทย (Thai)
• 🇬🇧 English (current)

Enjoy communicating! 😊
"""
    },
    
    'help': {
        'ru': """
🆘 **Справка по боту-переводчику**

**Основные функции:**
• Автоматический перевод сообщений
• Поддержка русского 🇷🇺, тайского 🇹🇭 и английского 🇬🇧 языков
• Обработка голосовых сообщений 🎤

**Команды:**
/start - информация о боте
/help - эта справка
/lang - установить родной язык
/config - настройки бота

**Как это работает:**
1. 📥 Отправьте текст или голосовое сообщение
2. 🔍 Бот определит язык
3. 🔄 Выполнит перевод
4. 📤 Отправит результат

**В групповых чатах:**
• Добавьте бота в группу
• Дайте права на чтение сообщений
• Админ должен включить бота командой /enable

Приятного использования! 😊
""",
        'th': """
🆘 **คู่มือบอทแปลภาษา**

**ฟังก์ชันหลัก:**
• แปลข้อความอัตโนมัติ
• รองรับภาษารัสเซีย 🇷🇺 ไทย 🇹🇭 และอังกฤษ 🇬🇧
• ประมวลผลข้อความเสียง 🎤

**คำสั่ง:**
/start - ข้อมูลเกี่ยวกับบอท
/help - คู่มือนี้
/lang - ตั้งค่าภาษาแม่
/config - การตั้งค่าบอท

**วิธีการทำงาน:**
1. 📥 ส่งข้อความหรือข้อความเสียง
2. 🔍 บอทจะระบุภาษา
3. 🔄 ทำการแปล
4. 📤 ส่งผลลัพธ์

**ในแชทกลุ่ม:**
• เพิ่มบอทในกลุ่ม
• ให้สิทธิ์ในการอ่านข้อความ
• ผู้ดูแลต้องเปิดใช้งานบอทด้วยคำสั่ง /enable

ขอให้สนุกกับการใช้งาน! 😊
""",
        'en': """
🆘 **Translator Bot Help**

**Main Features:**
• Automatic message translation
• Support for Russian 🇷🇺, Thai 🇹🇭, and English 🇬🇧
• Voice message processing 🎤

**Commands:**
/start - bot information
/help - this help
/lang - set native language
/config - bot settings

**How it Works:**
1. 📥 Send text or voice message
2. 🔍 Bot detects language
3. 🔄 Performs translation
4. 📤 Sends result

**In Group Chats:**
• Add bot to group
• Grant message reading rights
• Admin must enable bot with /enable command

Enjoy using the bot! 😊
"""
    },
    
    'config': {
        'ru': """
⚙️ **Настройки бота**

{admin_section}

**Ваши текущие настройки:**
• Родной язык: {native_lang}
• Модель перевода: {translation_model}
• Модель распознавания речи: {stt_model}

**Доступные команды:**
/lang [ru|th|en] - изменить родной язык
{admin_commands}

Для получения справки используйте /help
""",
        'th': """
⚙️ **การตั้งค่าบอท**

{admin_section}

**การตั้งค่าปัจจุบันของคุณ:**
• ภาษาแม่: {native_lang}
• โมเดลการแปล: {translation_model}
• โมเดลรู้จำเสียง: {stt_model}

**คำสั่งที่ใช้ได้:**
/lang [ru|th|en] - เปลี่ยนภาษาแม่
{admin_commands}

ใช้ /help สำหรับความช่วยเหลือ
""",
        'en': """
⚙️ **Bot Settings**

{admin_section}

**Your Current Settings:**
• Native language: {native_lang}
• Translation model: {translation_model}
• Speech recognition model: {stt_model}

**Available Commands:**
/lang [ru|th|en] - change native language
{admin_commands}

Use /help for assistance
"""
    },
    
    'config_admin_section': {
        'ru': """**🔐 Административные настройки**
Вы являетесь администратором бота и имеете доступ к расширенным настройкам.""",
        'th': """**🔐 การตั้งค่าผู้ดูแลระบบ**
คุณเป็นผู้ดูแลบอทและมีสิทธิ์เข้าถึงการตั้งค่าขั้นสูง""",
        'en': """**🔐 Administrative Settings**
You are a bot administrator and have access to advanced settings."""
    },
    
    'config_non_admin_section': {
        'ru': """**💎 Расширенные возможности**
Для получения доступа к расширенным настройкам приобретите подписку на neurorancho.com""",
        'th': """**💎 ฟีเจอร์ขั้นสูง**
ซื้อการสมัครสมาชิกที่ neurorancho.com เพื่อเข้าถึงการตั้งค่าขั้นสูง""",
        'en': """**💎 Advanced Features**
Purchase a subscription at neurorancho.com to access advanced settings"""
    },
    
    'config_admin_commands': {
        'ru': """• /model [название] - изменить модель перевода
• /stt [название] - изменить модель распознавания речи
• /enable - включить бота в группе
• /disable - выключить бота в группе""",
        'th': """• /model [ชื่อ] - เปลี่ยนโมเดลการแปล
• /stt [ชื่อ] - เปลี่ยนโมเดลรู้จำเสียง
• /enable - เปิดใช้งานบอทในกลุ่ม
• /disable - ปิดใช้งานบอทในกลุ่ม""",
        'en': """• /model [name] - change translation model
• /stt [name] - change speech recognition model
• /enable - enable bot in group
• /disable - disable bot in group"""
    },
    
    'lang_help': {
        'ru': """
🌐 **Настройка языка**

Укажите ваш родной язык:
• 🇷🇺 Русский: /lang ru
• 🇹🇭 Тайский: /lang th
• 🇬🇧 Английский: /lang en

Текущий язык: {current_lang}
""",
        'th': """
🌐 **การตั้งค่าภาษา**

ระบุภาษาแม่ของคุณ:
• 🇷🇺 ภาษารัสเซีย: /lang ru
• 🇹🇭 ภาษาไทย: /lang th
• 🇬🇧 ภาษาอังกฤษ: /lang en

ภาษาปัจจุบัน: {current_lang}
""",
        'en': """
🌐 **Language Settings**

Specify your native language:
• 🇷🇺 Russian: /lang ru
• 🇹🇭 Thai: /lang th
• 🇬🇧 English: /lang en

Current language: {current_lang}
"""
    },
    
    'lang_error': {
        'ru': "Неподдерживаемый язык. Доступные языки:",
        'th': "ไม่รองรับภาษานี้ ภาษาที่ใช้ได้:",
        'en': "Unsupported language. Available languages:"
    },
    
    'lang_success': {
        'ru': "✅ Родной язык установлен: {lang_name}",
        'th': "✅ ตั้งค่าภาษาแม่เป็น: {lang_name}",
        'en': "✅ Native language set to: {lang_name}"
    },
    
    'edit_prompt': {
        'ru': "🔄 Пожалуйста, опишите, что нужно исправить в переводе:",
        'th': "🔄 โปรดอธิบายว่าต้องการแก้ไขการแปลอย่างไร:",
        'en': "🔄 Please describe what needs to be corrected in the translation:"
    }
}