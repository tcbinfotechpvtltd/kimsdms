from django.urls import path
from .views import RolesListCreateAPIView, RolesRetrieveUpdateDestroyAPIView
from .views import RecordListCreateView, RecordRetrieveUpdateDestroyView



urlpatterns = [
    path('roles/', RolesListCreateAPIView.as_view(), name='roles-list-create'),
    path('roles/<int:id>/', RolesRetrieveUpdateDestroyAPIView.as_view(), name='roles-detail'),
    path('records/', RecordListCreateView.as_view(), name='record-list-create'),  # for List and Create
    path('records/<int:pk>/', RecordRetrieveUpdateDestroyView.as_view(), name='record-retrieve-update-destroy'),  # for Retrieve, Update, and Delete

]