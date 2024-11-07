from django.urls import path

from users.auth_views import LoginView
from .views import  UserView, UserCreate, UserDetail, UserSapUpdate, UserSoftDelete,UserUpdate

urlpatterns = [
    path('', UserView.as_view(), name='user-list'),
    path('sap-create/', UserCreate.as_view(), name='user-create'),
    path('<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('current-user/', UserDetail.as_view(), name='user-detail-by-token'),
    path('<int:pk>/sap-update/', UserSapUpdate.as_view(), name='user-sap-update'),
    path('<int:pk>/update/', UserUpdate.as_view(), name='user-update'),
    path('<int:pk>/delete/', UserSoftDelete.as_view(), name='user-soft-delete'),

] + [
    path('sign-in/', LoginView.as_view())

]