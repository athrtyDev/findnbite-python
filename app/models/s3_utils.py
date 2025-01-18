import boto3
import os
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
from io import BytesIO

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

    def compress_image(self, image_data, max_size=(800, 800), quality=85):
        """
        Compress image using PIL
        :param image_data: Binary image data
        :param max_size: Maximum dimensions (width, height)
        :param quality: JPEG compression quality (1-100)
        :return: Compressed image data in bytes
        """
        try:
            # Open image using PIL
            img = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if larger than max_size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save compressed image to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
        except Exception as e:
            print(f"Error compressing image: {str(e)}")
            return image_data  # Return original if compression fails

    def upload_file(self, file_data, folder, restaurant_name=None):
        """
        Upload a file to S3 with compression for images
        :param file_data: File data to upload
        :param folder: Folder type (logos, images, menus)
        :param restaurant_name: Name of the restaurant for folder organization
        """
        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4().hex}"
            
            if hasattr(file_data, 'filename'):
                # FileStorage object
                original_filename = secure_filename(file_data.filename)
                content = file_data.read()
                file_ext = os.path.splitext(original_filename)[1].lower()
                content_type = mimetypes.guess_type(original_filename)[0]

                # Compress if it's an image
                if content_type and content_type.startswith('image/'):
                    content = self.compress_image(
                        content,
                        max_size=(400, 400),
                        quality=90
                    )
                    file_ext = '.jpg'
                    content_type = 'image/jpeg'
            else:
                content = file_data
                file_ext = '.jpg'
                content_type = 'image/jpeg'

            # Create final filename
            final_filename = f"{unique_filename}{file_ext}"
            
            # Create S3 path based on restaurant name
            if restaurant_name:
                # Clean restaurant name (remove spaces and special characters)
                clean_name = "".join(c for c in restaurant_name if c.isalnum()).lower()
                s3_path = f"restaurants/{clean_name}/{folder}/{final_filename}"
            else:
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