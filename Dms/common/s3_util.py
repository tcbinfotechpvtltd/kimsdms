from django.utils import timezone
import boto3, os
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError
from rest_framework.exceptions import NotFound


class S3Storage(object):
    def __init__(self, **kwargs):
        self.session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY
        )

        self.s3 = self.session.resource('s3')


    def upload_s3_file(self, local_source_path, file_relative_path, bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        object = self.s3.Object(bucket_name, file_relative_path)
        params = {
            'Metadata' :{
                'first_created_at': timezone.now().isoformat()
            }            
        }

        # Having to add this object.content_length because otherwise getting this error while uploading file for school activity export-
        # *** botocore.exceptions.ClientError: An error occurred (IllegalLocationConstraintException) when calling the PutObject operation: The ap-southeast-3 location constraint is incompatible for the region specific endpoint this request was sent to.        
        try:
            object.content_length
        except: pass
        result = object.put(Body=open(local_source_path, 'rb'), CacheControl='no-cache', **params)

        res = result.get('ResponseMetadata')

        if res.get('HTTPStatusCode') == 200:
            return file_relative_path
        else:
            return -1
        
    @classmethod
    def upload_file_obj_to_s3(self, file, path):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        try:
            s3_client.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, path)
            file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{path}"
            return file_url
        except (NoCredentialsError, ClientError) as e:
            raise NotFound(f"Failed to upload file to S3: {str(e)}")
        
