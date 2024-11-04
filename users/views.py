from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from .models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import RecordLogSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import generics
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError
import boto3,os

# Create your views here.
class UserCreate(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()  #
    
class UserView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_delete=False)# Define the queryset to return all users

class UserDetail(RetrieveAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all() 

    def get_object(self):
        pk = self.kwargs.get('pk')
        token = self.request.headers.get('Authorization').split()[1]
        try:
            if pk:
                return get_object_or_404(User, pk=pk, is_delete=False)
            elif token:
                token = get_object_or_404(Token, key=token)
                if not token.user.is_delete:
                    user = token.user
                    return user
                else:
                    raise NotFound("User does not exist.")
            else:
                raise NotFound("User identifier not provided.")
        except Http404:
            raise NotFound("User does not exist.")
        
    def retrieve(self, request, *args, **kwargs):
        # Retrieve the user instance using the get_object method
        user = self.get_object()
        
        # Get user roles and construct roles data
        user_roles = user.roles.values('id', 'role_name', 'prev_level')
        roles_data = [
            {
                "id": role["id"],
                "role_name": role["role_name"],
                'is_initial_role': True if role['prev_level'] is None else False
            }
            for role in user_roles
        ]
        
        # Serialize the user data once
        user_data = self.get_serializer(user).data
        user_data['roles'] = roles_data
        
        # Return the final data in the response
        return Response(user_data)
class UserUpdate(UpdateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        try:
            return get_object_or_404(User, pk=self.kwargs['pk'])
        except Http404:
            raise NotFound("User does not exist.")

    def upload_to_s3(self, file, path):
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

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        print("rohit==>",request.FILES)
        photo = request.FILES.get('photo')
        signature = request.FILES.get('signature')

        # Upload files to S3 and update URLs in user instance
        if photo:
            photo_extension = os.path.splitext(photo.name)[1]
            photo_path = f"user/{user.id}/profile_pic{photo_extension}"
            user.photo = self.upload_to_s3(photo, photo_path)
            print("rohit==>",user)

        if signature:
            signature_path = f"user_signatures/{user.id}/signature"
            user.signature_url = self.upload_to_s3(signature, signature_path)
        
        user.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSoftDelete(DestroyAPIView):
    queryset = User.objects.all()

    def get_object(self):
        try:
            user = get_object_or_404(User, pk=self.kwargs['pk'], is_delete=False)
            return user
        except Http404:
            raise NotFound("User does not exist.")

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_delete = True  # Soft delete the user
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
