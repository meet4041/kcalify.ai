import os
from google.cloud import storage
from uuid import uuid4

# The name of the GCS bucket where user images will be stored
# Set this as an environment variable in your Cloud Run deployment
STORAGE_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "nutrition-scanner-uploads") 

class ImageProcessor:
    """Handles image storage operations using Google Cloud Storage."""
    
    def __init__(self):
        try:
            # Client automatically authenticates using the service account credentials 
            # assigned to the Cloud Run service.
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(STORAGE_BUCKET_NAME)
        except Exception as e:
            print(f"WARNING: Google Cloud Storage client initialization failed. Ensure GCS_BUCKET_NAME is set and service account has access. Error: {e}")
            self.storage_client = None
            self.bucket = None

    def upload_image_to_storage(self, user_id: str, image_bytes: bytes, mime_type: str) -> str:
        """
        Uploads image bytes to GCS and returns the public access URL.
        
        Args:
            user_id: Used to organize files in the bucket.
            image_bytes: The raw image content.
            mime_type: The MIME type of the file.
            
        Returns: The public URL of the stored image.
        """
        if not self.bucket:
            raise Exception("Image storage bucket not initialized. Cannot upload image.")

        # Generate a unique filename: user_id/uuid.jpg (or .png)
        file_extension = mime_type.split('/')[-1] if '/' in mime_type else 'jpg'
        filename = f"{user_id}/{uuid4()}.{file_extension}"
        
        try:
            blob = self.bucket.blob(filename)
            
            # The public access configuration is set via IAM/Bucket Policy, 
            # but we assume the deployment environment grants necessary permissions.
            blob.upload_from_string(image_bytes, content_type=mime_type)
            
            # Set public read permissions on the object (if bucket policy allows)
            blob.make_public()
            
            # Return the public URL
            return blob.public_url

        except Exception as e:
            print(f"GCS upload failed for user {user_id}: {e}")
            raise Exception("Failed to upload image to cloud storage.")

# Initialize a singleton processor
image_processor = ImageProcessor()