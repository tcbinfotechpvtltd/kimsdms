from django.urls import path
from .views import  UserView, UserCreate

urlpatterns = [
    path('users/', UserView.as_view(), name='user-list'),
    path('create/', UserCreate.as_view(), name='user-create'),
]