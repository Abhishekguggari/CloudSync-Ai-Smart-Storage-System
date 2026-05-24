import uuid

#create link
def generate_share_link(filename):
    token = uuid.uuid4()

    return f"http://127.0.0.1:5000/share/{filename}/{token}"