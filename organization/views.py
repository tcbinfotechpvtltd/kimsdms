from rest_framework import generics
from .models import Roles
from .serializers import RolesSerializer

class RolesListCreateAPIView(generics.ListCreateAPIView):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer


class RolesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    lookup_field = 'id'  #