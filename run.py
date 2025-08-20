#!/usr/bin/env python3
"""
Скрипт запуска Telegram Translator Bot
"""

import os
import sys

def check_environment():
    """Проверка переменных окружения"""
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENROUTER_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'YOUR_{var}':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Ошибка: Не установлены обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nУстановите переменные окружения:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("export OPENROUTER_API_KEY='your_api_key'")
        print("\nИли создайте файл .env с этими переменными")
        return False
    
    return True

def main():
    """Основная функция запуска"""
    print("🤖 Telegram Translator Bot")
    print("=" * 40)
    
    # Проверка переменных окружения
    if not check_environment():
        sys.exit(1)
    
    print("✅ Переменные окружения настроены")
    print("🚀 Запуск бота...")
    print("📝 Для остановки нажмите Ctrl+C")
    print("=" * 40)
    
    # Импорт и запуск бота
    try:
        from bot import main as bot_main
        import asyncio
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

