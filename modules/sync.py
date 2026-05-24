import boto3
from config import AWS_BUCKET, AWS_REGION
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

#sync to cloudgit
def sync_to_cloud(filepath):
    try:
        filename = filepath.split('/')[-1]

        s3.upload_file(filepath, AWS_BUCKET, filename)

        return 'Synced'

    except Exception as e:
        return 'Not Synced'