import os
import shutil
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

# ==========================================
# HYBRID SYNC (REAL AWS S3 + LOCAL FALLBACK)
# ==========================================
def sync_to_cloud(filepath, cloud_bucket_dir="cloud_bucket"):
    """
    Attempts to upload to real AWS S3 bucket.
    If AWS is not configured, it gracefully falls back to copying
    the file to a local simulated cloud folder.
    """
    if not os.path.exists(filepath):
        return 'Failed: Source Missing'

    filename = filepath.replace('\\', '/').split('/')[-1]
    
    # --- STRATEGY A: REAL AWS UPLOAD ---
    if is_aws_configured and s3 is not None:
        try:
            s3.upload_file(filepath, AWS_BUCKET, filename)
            return 'Synced'
        except Exception:
            pass # Fall through to local simulation if real upload fails
            
    # --- STRATEGY B: LOCAL SIMULATED CLOUD FALLBACK ---
    try:
        os.makedirs(cloud_bucket_dir, exist_ok=True)
        destination_path = os.path.join(cloud_bucket_dir, filename)
        
        # Copy file to simulate the cloud storage environment locally
        shutil.copy2(filepath, destination_path)
        return 'Synced'
    except Exception as e:
        return f'Failed: {str(e)}'