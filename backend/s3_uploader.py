import boto3, os
from io import BytesIO

# This works for BOTH local MinIO and real AWS S3
# When AWS_ENDPOINT_URL is set → uses MinIO
# When it's not set → uses real AWS S3 automatically
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),  # None on real AWS
)

BUCKET = os.getenv("S3_BUCKET_NAME", "retail-shelf-frames")

async def upload_frame(image_bytes: bytes, timestamp: float) -> str:
    key = f"frames/{int(timestamp)}.jpg"
    # Create bucket if it doesn't exist (MinIO only)
    try:
        s3.head_bucket(Bucket=BUCKET)
    except:
        s3.create_bucket(Bucket=BUCKET)
    
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=BytesIO(image_bytes),
        ContentType="image/jpeg"
    )
    return key