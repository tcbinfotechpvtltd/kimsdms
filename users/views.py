from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from rest_framework import status
from .serializers import UserSerializer

# Create your views here.
class UserCreate(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()  #
    
class UserView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()  # Define the queryset to return all users
