import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")
AWS_REGION = os.getenv("aws_region")
S3_BUCKET = os.getenv("s3_bucket")
