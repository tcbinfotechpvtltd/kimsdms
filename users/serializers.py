from rest_framework import serializers
from .models import User
from organization.models import Roles, Organization

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'name']  # Assuming Roles has 'id' and 'name' fields

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
    roles = RolesSerializer(many=True, read_only=True)  # Read-only field for roles
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(), 
        many=True, 
        write_only=True, 
        required=False,  # Make it non-mandatory
        allow_null=True,  # Allow null values
        source='roles'
    )


    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'is_admin', 'is_active',
            'organization', 'organization_id', 'roles', 'role_ids',"first_name","last_name"
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
        }

    def validate(self, data):
        # Check if email is unique
        email = data.get('email')
        if self.instance and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
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

    
    