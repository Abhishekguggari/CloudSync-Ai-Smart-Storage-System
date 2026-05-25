import os
import hashlib

UPLOAD_FOLDER = "uploads"

# AI CATEGORY DETECTION

def categorize_file(filename):

    extension = filename.split('.')[-1].lower()

    if extension in ['jpg', 'png', 'jpeg']:

        return "Image"

    elif extension in ['pdf', 'docx', 'txt']:

        return "Document"

    elif extension in ['mp4', 'mkv']:

        return "Video"

    else:

        return "Other"

# DUPLICATE DETECTION

def file_hash(filepath):

    hasher = hashlib.md5()

    with open(filepath, 'rb') as file:

        buffer = file.read()

        hasher.update(buffer)

    return hasher.hexdigest()

def detect_duplicate(filename):

    current_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    if not os.path.exists(current_path):

        return "No"

    current_hash = file_hash(current_path)

    for existing_file in os.listdir(UPLOAD_FOLDER):

        existing_path = os.path.join(
            UPLOAD_FOLDER,
            existing_file
        )

        if existing_file != filename:

            existing_hash = file_hash(existing_path)

            if current_hash == existing_hash:

                return "Duplicate Found"

    return "No Duplicate"