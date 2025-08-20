#!/usr/bin/env python3
"""
Тестовый скрипт для проверки основных функций бота
"""

import os
import sys

def test_imports():
    """Тест импорта всех модулей"""
    print("🧪 Тестирование импортов...")
    
    try:
        import config
        print("✅ config.py - OK")
        
        import user_storage
        print("✅ user_storage.py - OK")
        
        import language_detector
        print("✅ language_detector.py - OK")
        
        import openrouter_service
        print("✅ openrouter_service.py - OK")
        
        # Не импортируем bot.py, так как он требует токены
        print("✅ Все модули импортированы успешно")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_user_storage():
    """Тест системы хранения пользователей"""
    print("\n🧪 Тестирование хранения пользователей...")
    
    try:
        from user_storage import UserStorage
        
        # Создаем тестовое хранилище
        storage = UserStorage('test_users.json')
        
        # Тестируем создание пользователя
        user = storage.get_user(12345)
        assert user['user_id'] == 12345
        assert user['native_language'] == 'ru'
        print("✅ Создание пользователя - OK")
        
        # Тестируем обновление настроек
        storage.set_native_language(12345, 'th')
        user = storage.get_user(12345)
        assert user['native_language'] == 'th'
        print("✅ Обновление настроек - OK")
        
        # Очистка тестового файла
        if os.path.exists('test_users.json'):
            os.remove('test_users.json')
        
        print("✅ Система хранения работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования хранилища: {e}")
        return False

def test_language_detector():
    """Тест определения языка"""
    print("\n🧪 Тестирование определения языка...")
    
    try:
        from language_detector import LanguageDetector
        
        detector = LanguageDetector()
        
        # Тестируем определение русского
        lang = detector.detect_language("Привет, как дела?")
        print(f"   Русский текст определен как: {lang}")
        
        # Тестируем определение английского
        lang = detector.detect_language("Hello, how are you?")
        print(f"   Английский текст определен как: {lang}")
        
        # Тестируем определение целевого языка
        target = detector.determine_target_language('ru')
        assert target == 'th'
        print("✅ Определение целевого языка - OK")
        
        print("✅ Определение языка работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования детектора: {e}")
        return False

def test_config():
    """Тест конфигурации"""
    print("\n🧪 Тестирование конфигурации...")
    
    try:
        import config
        
        # Проверяем наличие основных настроек
        assert hasattr(config, 'SUPPORTED_LANGUAGES')
        assert hasattr(config, 'DEFAULT_TRANSLATION_MODEL')
        assert hasattr(config, 'TRANSLATION_PROMPTS')
        
        # Проверяем поддерживаемые языки
        assert 'ru' in config.SUPPORTED_LANGUAGES
        assert 'th' in config.SUPPORTED_LANGUAGES
        assert 'en' in config.SUPPORTED_LANGUAGES
        
        print("✅ Конфигурация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🤖 Тестирование Telegram Translator Bot")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_user_storage,
        test_language_detector
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        print("🚀 Бот готов к запуску!")
    else:
        print("⚠️  Некоторые тесты не пройдены")
        print("🔧 Проверьте ошибки выше")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

