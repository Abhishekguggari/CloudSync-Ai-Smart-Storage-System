from flask import session

def get_settings():
    """
    Fetches preference values dynamically from the current session.
    If the user hasn't configured them yet, defaults everything to 'Enabled'.
    """
    return {
        "cloud_sync": session.get('cloud_sync', 'Enabled'),
        "encryption": session.get('encryption', 'Enabled'),
        "ai_features": session.get('ai_features', 'Enabled'),
        "notifications": session.get('notifications', 'Disabled')
    }