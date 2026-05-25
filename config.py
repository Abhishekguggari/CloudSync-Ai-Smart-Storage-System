import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MAX_STORAGE = 1024 * 1024 * 1024 * 5
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg',
    'docx', 'mp4', 'zip'
}

AWS_BUCKET = 'your_bucket_name'
AWS_REGION = 'ap-south-1'
AWS_ACCESS_KEY = 'your_key'
AWS_SECRET_KEY = 'your_secret'