from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import LoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="User login to obtain a token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the user'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password of the user'),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Response(
                description="Token and user details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication Token'),
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                        'is_admin': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is the user an admin?'),
                        'user_name': openapi.Schema(type=openapi.TYPE_STRING,description='Username')
                    }
                )
            ),
            401: openapi.Response(description="Invalid credentials")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = authenticate(username=data['username'], password=data['password'])
        if user:
            token, created = Token.objects.get_or_create(user=user)
            user_roles = user.roles.values("id", "organization__id", "organization__name", "role_name",
                                           'prev_level', 'can_update_fields', 'update_allowed_fields'
                                           )

            roles_data = [
                {
                    "id": role["id"],
                    "organization_id": role["organization__id"],
                    "organization_name": role["organization__name"],  # Rename here
                    "role_name": role["role_name"],
                    'prev_level': role['prev_level'],
                    'is_initial_role': True if role['prev_level'] is None else False,
                    'can_update_fields': role['can_update_fields'],
                    'update_allowed_fields': role['update_allowed_fields']

                }
                for role in user_roles
            ]
            return Response({'token': token.key, 'user_id': user.id, 'is_admin': user.is_admin, 'username': user.username,"first_name": user.first_name, "last_name": user.last_name, "email": user.email, "roles": roles_data})
        else:
            return Response({'error': 'Invalid credentials'}, status=401)