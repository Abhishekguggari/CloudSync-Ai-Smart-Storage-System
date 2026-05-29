import json
import os

SETTINGS_FILE = 'settings.json'

def get_settings(username='default'):
    default_settings = {
        'cloud_sync': 'Enabled',
        'encryption': 'Enabled',
        'ai_features': 'Enabled',
        'dark_mode': 'Disabled',
        'notifications': 'Enabled'
    }
    
    if not os.path.exists(SETTINGS_FILE):
        return default_settings
        
    with open(SETTINGS_FILE, 'r') as f:
        try:
            data = json.load(f)
            user_data = data.get(username, {})
            # Merge missing keys with default values
            for k, v in default_settings.items():
                if k not in user_data:
                    user_data[k] = v
            return user_data
        except json.JSONDecodeError:
            return default_settings

def save_settings(username, settings_data):
    data = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
                
    data[username] = settings_data
    
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4)