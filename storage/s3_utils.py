import boto3
import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def generate_s3_object_key(source: str, file_type: str, file_extension: str) -> str:
    """
    Generate a structured S3 object key (path).

    Args:
        source (str): The source of the file (e.g., 'processed_pdfs', 'scraped_websites').
        file_type (str): The type of the file (e.g., 'markdown', 'images', 'html').
        file_extension (str): The file extension (e.g., '.md', '.png', '.html').

    Returns:
        str: A structured S3 object key.
    """
    today = datetime.now()
    date_prefix = today.strftime("%Y/%m/%d")  # Partition by year/month/day
    unique_id = uuid4().hex  # Generate a unique identifier
    return f"{source}/{file_type}/{date_prefix}/{unique_id}{file_extension}"

    
def upload_file_to_s3(file_path: str, source: str, file_type: str, metadata: dict = None) -> str:
    """
    Upload a file to S3 with structured naming.

    Args:
        file_path (str): Local path of the file to upload.
        source (str): File source (e.g., 'processed_pdfs', 'scraped_websites').
        file_type (str): File type (e.g., 'markdown', 'images', 'html').
        metadata (dict): Optional metadata tags for the object.

    Returns:
        str: Public URL of the uploaded file.
    """
    # Extract the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    # Determine file type based on the extension
    extension_to_type = {
        ".md": "markdown",
        ".txt": "text",
        ".png": "images",
        ".jpg": "images",
        ".jpeg": "images",
        ".pdf": "pdfs",
        ".html": "html"
    }
    file_type = extension_to_type.get(file_extension, "other")  # Default to 'other' for unknown types

    # Generate a structured S3 object key
    object_key = generate_s3_object_key(source, file_type, file_extension)

    try:
        # Upload the file to S3
        s3_client.upload_file(
            file_path, S3_BUCKET_NAME, object_key,
            ExtraArgs={
                "Metadata": metadata or {},  # Add metadata
                "ServerSideEncryption": "AES256"  # Enable encryption
            }
        )
        # Return the public S3 URL
        return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
    except Exception as e:
        raise RuntimeError(f"Error uploading {file_path} to S3: {str(e)}")
