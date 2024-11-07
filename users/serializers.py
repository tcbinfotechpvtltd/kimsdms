from rest_framework import serializers
from .models import RecordLog, User
from rest_framework.exceptions import ValidationError
from organization.models import Roles, Organization

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
    photo = serializers.SerializerMethodField()
    signature = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'is_admin', 'is_active',
            'organization', 'organization_id', 'roles', 'role_ids',"first_name","last_name","photo","signature","contact"
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
        }

    def get_photo(self, obj):
        # Return the relative path without MEDIA_URL
        return obj.photo.name if obj.photo else None
    
    def get_signature(self, obj):
        # Return the relative path without MEDIA_URL
        return obj.signature.name if obj.signature else None


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
        print("username==>",username)
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