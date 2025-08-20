import json
import os
from typing import Dict, Any
from config import DEFAULT_TRANSLATION_MODEL, DEFAULT_STT_MODEL

class UserStorage:
    def __init__(self, storage_file='users.json'):
        self.storage_file = storage_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from JSON file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user settings or create default"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                'user_id': user_id,
                'username': None,
                'translation_model': DEFAULT_TRANSLATION_MODEL,
                'stt_model': DEFAULT_STT_MODEL,
                'native_language': 'ru'  # Default to Russian
            }
            self._save_users()
        
        return self.users[user_id_str]
    
    def update_user(self, user_id: int, **kwargs):
        """Update user settings"""
        user_id_str = str(user_id)
        user = self.get_user(user_id)
        
        for key, value in kwargs.items():
            if key in user:
                user[key] = value
        
        self._save_users()
        return user
    
    def set_native_language(self, user_id: int, language: str):
        """Set user's native language"""
        return self.update_user(user_id, native_language=language)
    
    def set_translation_model(self, user_id: int, model: str):
        """Set user's translation model"""
        return self.update_user(user_id, translation_model=model)
    
    def set_stt_model(self, user_id: int, model: str):
        """Set user's STT model"""
        return self.update_user(user_id, stt_model=model)

