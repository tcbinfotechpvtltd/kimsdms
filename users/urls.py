from django.urls import path

from users.auth_views import LoginView
from .views import  UserView, UserCreate, UserDetail, UserUpdate, UserSoftDelete

urlpatterns = [
    path('', UserView.as_view(), name='user-list'),
    path('create/', UserCreate.as_view(), name='user-create'),
    path('<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('<int:pk>/update/', UserUpdate.as_view(), name='user-update'),
    path('<int:pk>/delete/', UserSoftDelete.as_view(), name='user-soft-delete'),

] + [
    path('sign-in/', LoginView.as_view())

]