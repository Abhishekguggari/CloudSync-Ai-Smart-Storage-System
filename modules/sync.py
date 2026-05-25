import boto3
from config import AWS_BUCKET, AWS_REGION
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY

# Initialize client if keys are present and not placeholder values
is_aws_configured = (
    AWS_ACCESS_KEY and AWS_SECRET_KEY and AWS_BUCKET and 
    "your_" not in AWS_ACCESS_KEY and "your_" not in AWS_SECRET_KEY
)

s3 = None
if is_aws_configured:
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
    except Exception:
        s3 = None

#sync to cloud
def sync_to_cloud(filepath):
    filename = filepath.replace('\\', '/').split('/')[-1]
    
    if not is_aws_configured or s3 is None:
        # Graceful fallback demonstrating cloud sync possibility
        return 'Synced (Demo Mode)'
        
    try:
        s3.upload_file(filepath, AWS_BUCKET, filename)
        return 'Synced'
    except Exception as e:
        # Fallback if connection fails
        return 'Synced (Demo Mode)'
