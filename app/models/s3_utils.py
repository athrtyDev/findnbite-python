import boto3
import os
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

class S3Uploader:
    def __init__(self):
        # Validate required environment variables
        self.bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        self.region = os.getenv('AWS_S3_REGION_NAME')
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

        # Print debug info (remove in production)
        print(f"Initializing S3 with bucket: {self.bucket}, region: {self.region}")
        print(f"Access Key ID: {self.access_key[:4]}...{self.access_key[-4:]}")

        if not all([self.bucket, self.region, self.access_key, self.secret_key]):
            raise ValueError("Missing required AWS credentials in environment variables")

        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            # Test connection
            self.s3.list_buckets()
            print("Successfully connected to AWS S3")
        except Exception as e:
            print(f"Failed to connect to AWS S3: {str(e)}")
            raise

    def upload_file(self, file_data, folder):
        """
        Upload a file to S3
        :param file_data: File data (can be FileStorage or bytes)
        :param folder: S3 folder name (e.g., 'logos', 'images', 'menus')
        :return: URL of uploaded file
        """
        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4().hex}"
            
            # Handle different file types
            if hasattr(file_data, 'filename'):
                # FileStorage object
                original_filename = secure_filename(file_data.filename)
                content = file_data.read()
                file_ext = os.path.splitext(original_filename)[1].lower()
                content_type = mimetypes.guess_type(original_filename)[0]
            else:
                # Bytes object
                content = file_data
                file_ext = '.jpg'  # Default to jpg for binary data
                content_type = 'image/jpeg'

            # Create final filename
            final_filename = f"{unique_filename}{file_ext}"
            s3_path = f"restaurants/{folder}/{final_filename}"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_path,
                Body=content,
                ContentType=content_type or 'application/octet-stream'
            )
            
            # Generate URL
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_path}"
            return url
            
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            raise

    def delete_file(self, url):
        """
        Delete a file from S3
        :param url: Full URL of the file to delete
        """
        try:
            # Extract key from URL
            key = url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[1]
            
            # Delete from S3
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            
        except Exception as e:
            print(f"Error deleting from S3: {str(e)}")
            raise 