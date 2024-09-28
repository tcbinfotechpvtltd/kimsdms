from django.urls import path
from .views import RolesListCreateAPIView, RolesRetrieveUpdateDestroyAPIView


urlpatterns = [
    path('roles/', RolesListCreateAPIView.as_view(), name='roles-list-create'),
    path('roles/<int:id>/', RolesRetrieveUpdateDestroyAPIView.as_view(), name='roles-detail'),
]