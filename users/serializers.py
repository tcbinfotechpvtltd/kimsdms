from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username','password', 'email', 'is_admin', 'is_active']
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
            'password': {'write_only': True}  # Assuming you want to handle password in the API
        }

    def validate(self, data):
        # Check if email is unique
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        return data

    # def create(self, validated_data):
    #     roles_data = validated_data.pop('roles', [])
    #     user = User(**validated_data)
    #     user.set_password(validated_data['password'])
    #     user.save()
    #     user.roles.set(roles_data)  # Assign roles if provided
    #     return user