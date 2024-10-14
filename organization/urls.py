from django.urls import path
from .views import DepartmentListView, DocumentCreateAPI, DocumentDeleteAPI, RecordCreateView, RecordListView, RolesListCreateAPIView, RolesRetrieveUpdateDestroyAPIView, SapRecordCreateView, generate_report_pdf
from .views import RecordRetrieveUpdateDestroyView, ActionAPIView



urlpatterns = [
    path('roles/', RolesListCreateAPIView.as_view(), name='roles-list-create'),
    path('roles/<int:id>/', RolesRetrieveUpdateDestroyAPIView.as_view(), name='roles-detail'),
    path('sap-records-create/', SapRecordCreateView.as_view(), name='sap-record-create'),  
    path('records/', RecordListView.as_view(), name='record-list-'),  
    path('records/<int:pk>/', RecordRetrieveUpdateDestroyView.as_view(), name='record-retrieve-update-destroy'),  # for Retrieve, Update, and Delete
    # path('upload-document/', DocumentCreateAPI.as_view(), name='DocumentCreateAPI'),
    path('delete-document/<int:pk>', DocumentDeleteAPI.as_view(), name='DocumentDeleteAPI'),
    path('departments/', DepartmentListView.as_view(), name='DepartmentListView'),
    path('take-action/', ActionAPIView.as_view(), name='ActionAPIView'),
    path('generate-report/', generate_report_pdf, name='generate_report_pdf')
    


]