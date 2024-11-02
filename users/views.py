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
                    return token.user
                else:
                    raise NotFound("User does not exist.")
            else:
                raise NotFound("User identifier not provided.")
        except Http404:
            raise NotFound("User does not exist.")
        
class UserUpdate(UpdateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        try:
            return get_object_or_404(User, pk=self.kwargs['pk'])
        except Http404:
            raise NotFound("User does not exist.")

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
