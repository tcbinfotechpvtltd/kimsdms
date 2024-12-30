import os
from rest_framework import serializers
import ast
from Dms.common.s3_util import S3Storage
from .models import RecordLog, User
from rest_framework.exceptions import ValidationError
from organization.models import Roles, Organization
from django.db import transaction
from django.conf import settings

class RolesDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'role_name']  # Assuming Roles has 'id' and 'name' fields

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']  # Assuming Organization has 'id' and 'name' fields

class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)  # Read-only field to show organization details
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        write_only=True, 
        required=False,  # Make it non-mandatory
        allow_null=True,  # Allow null values
        source='organization'
    )
    roles = RolesDataSerializer(many=True, read_only=True)  # Read-only field for roles
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(), 
        many=True, 
        write_only=True, 
        required=False,  # Make it non-mandatory
        allow_null=True,  # Allow null values
        source='roles'
    )
    photo = serializers.ImageField(required=False, allow_null=True)
    signature = serializers.ImageField(required=False, allow_null=True)


    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'is_admin', 'is_active','designation',
            'organization', 'organization_id', 'roles', 'role_ids',"first_name","last_name","photo","signature","contact"
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
        }

    def to_representation(self, instance):
        # Customize the representation of photo and signature URLs
        representation = super().to_representation(instance)
        if instance.photo:
            representation['photo'] = instance.photo.name  # Adjust as needed
        if instance.signature:
            representation['signature'] = instance.signature.name  # Adjust as needed
        return representation

    def validate_photo(self, value):
        if not value.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise serializers.ValidationError("Only image files are allowed for photo.")
        return value

    def validate_signature(self, value):
        if not value.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise serializers.ValidationError("Only image files are allowed for signature.")
        return value

    def validate(self, data):
        # Check if email is unique
        username = data.get('username')
        email = data.get('email')
        # Check for existing username
        if User.objects.filter(username=username).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        
        # Check for existing email
        if User.objects.filter(email=email).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return data

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        organization = validated_data.pop('organization', None)

        # Create user
        user = User.objects.create_user(**validated_data)
        if organization:
            user.organization = organization
        user.roles.set(roles)
        user.save()
        return user
    


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)



class UserSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', "first_name","last_name"
        ]




class RecordLogSerializer(serializers.ModelSerializer):

    created_by = UserSlimSerializer()

    followup_users = UserSlimSerializer(many=True)
    followup_user_hod = UserSlimSerializer()
    
    class Meta:
        model = RecordLog
        fields = '__all__'

    def to_representation(self, instance):
        rp = super().to_representation(instance)

        rp['doc'] = {
            "file_name": str(instance.doc.file.name).split('/')[-1],
            "url": instance.doc.file.url
        } if instance.doc and instance.doc.file else None

        return rp
    



class UserCreateSerializer(serializers.ModelSerializer):
    role_ids = serializers.CharField( # Ensure each item in the list is an integer (role ID)
        write_only=True
    )
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'is_admin',
            'organization', 'role_ids',"first_name","last_name","photo","signature","contact"
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.photo:
            representation['photo'] = instance.photo.url  
        if instance.signature:
            representation['signature'] = instance.signature.url  

        return representation

    def validate_photo(self, value):
        if not value.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise serializers.ValidationError("Only image files are allowed for photo.")
        return value

    def validate_signature(self, value):
        if not value.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise serializers.ValidationError("Only image files are allowed for signature.")
        return value

    def validate(self, data):
        # Check if email is unique
        username = data.get('username')
        email = data.get('email')
        # # Check for existing username
        # if User.objects.filter(username=username).exclude(id=self.instance.id if self.instance else None).exists():
        #     raise serializers.ValidationError({"username": "This username is already in use."})
        
        if User.objects.filter(email=email).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        validated_data['role_ids'] = ast.literal_eval(validated_data['role_ids']) if isinstance(validated_data['role_ids'], str) else validated_data['role_ids']
        roles = validated_data.pop('role_ids', '')
        photo = validated_data.pop('photo', None)
        signature = validated_data.pop('signature', None)
        validated_data['organization_id'] =1
        user = User.objects.create_user(**validated_data)

        roles_data = roles
        if roles_data:
            user.roles.set(roles_data)
        s3 = S3Storage()
        if photo:
            user.photo = photo
            user.save()  # Save user first to upload photo to S3 and generate its name in the DB
            
            try:
                

                # Upload photo to S3
                photo_local_path = user.photo.path
                photo_relative_path = 'media/' + user.photo.url.split('media/')[1]
                res = s3.upload_s3_file(local_source_path=photo_local_path, file_relative_path=photo_relative_path)

                # Remove the local photo file
                if os.path.exists(photo_local_path):
                    os.unlink(photo_local_path)

                # Update photo URL in the database
                user.photo = f"{settings.MEDIA_URL}{user.photo.name}"  # Add MEDIA_URL to the file name

            except Exception as e:
                print(f"Error uploading photo to S3: {e}")
                # Handle error if needed (e.g., set a default image or leave the field as is)
                pass

        # Handle signature upload to S3 if provided
        if signature:
            user.signature = signature
            user.save()  # Save user first to upload signature to S3 and generate its name in the DB
            
            try:
                # Upload signature to S3
                signature_local_path = user.signature.path
                signature_relative_path = 'media/' + user.signature.url.split('media/')[1]
                res = s3.upload_s3_file(local_source_path=signature_local_path, file_relative_path=signature_relative_path)

                # Remove the local signature file
                if os.path.exists(signature_local_path):
                    os.unlink(signature_local_path)

                # Update signature URL in the database
                user.signature = f"{settings.MEDIA_URL}{user.signature.name}"  # Add MEDIA_URL to the file name

            except Exception as e:
                print(f"Error uploading signature to S3: {e}")
                # Handle error if needed (e.g., set a default signature or leave the field as is)
                pass
        user.save()

        return user
    