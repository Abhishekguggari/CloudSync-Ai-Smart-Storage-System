import os

from datetime import datetime

# CREATE LOGS FOLDER IF NOT EXISTS

os.makedirs(
    'logs',
    exist_ok=True
)

# ACTIVITY LOGGER

def log_activity(message):

    with open(
        'logs/activity.log',
        'a',
        encoding='utf-8'
    ) as log:

        log.write(
            f"[{datetime.now()}] {message}\n"
        )