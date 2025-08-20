#!/usr/bin/env python3
"""
Test script to verify environment variables loading
"""

import config

def test_config():
    print("Testing configuration loading...")
    print(f"TELEGRAM_BOT_TOKEN: {'✓ Set' if config.TELEGRAM_BOT_TOKEN else '✗ Not set'}")
    print(f"OPENROUTER_API_KEY: {'✓ Set' if config.OPENROUTER_API_KEY else '✗ Not set'}")
    
    if config.TELEGRAM_BOT_TOKEN and config.OPENROUTER_API_KEY:
        print("\n✅ All environment variables loaded successfully!")
    else:
        print("\n❌ Some environment variables are missing!")

if __name__ == "__main__":
    test_config() 