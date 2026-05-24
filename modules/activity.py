from datetime import datetime

# Activity logging
def log_activity(message):
    with open('logs/activity.log', 'a') as log:
        log.write(f"{datetime.now()} - {message}\n")