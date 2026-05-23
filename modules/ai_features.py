import os


def categorize_file(filename):
    extension = filename.split('.')[-1]

    image_types = ['png', 'jpg', 'jpeg']
    document_types = ['pdf', 'docx', 'txt']
    video_types = ['mp4']

    if extension in image_types:
        return 'Image'

    elif extension in document_types:
        return 'Document'

    elif extension in video_types:
        return 'Video'

    return 'Other'


def detect_duplicate(filename):
    upload_path = 'uploads'

    files = os.listdir(upload_path)

    count = files.count(filename)

    if count > 1:
        return 'Duplicate'

    return 'Unique'