from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from Dms.common.mixins import SoftDeleteMixin
from users.models import RecordLog
from .models import RecordDocument, RecordRoleStatus, Roles
from .serializers import ActionSerializer, DocumentSerializer, RecordListSerializer, RecordRetrieveSerializer, RolesSerializer, SapRecordSerializer
from .models import Record, DepartMent
from .serializers import RecordSerializer, DepartmentSerializer
from django_filters import rest_framework as filters
from django.db.models import Q, Case, When, Value
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class DepartmentListView(generics.ListAPIView):
    queryset = DepartMent.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['organization']
 


class RolesListCreateAPIView(generics.ListCreateAPIView):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer


class RolesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    lookup_field = 'id'  #


class RecordCreateView(generics.CreateAPIView):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer


class SapRecordCreateView(generics.CreateAPIView):
    queryset = Record.objects.all()
    serializer_class = SapRecordSerializer



class RecordListView(generics.ListAPIView):
    queryset = Record.objects.all()
    serializer_class = RecordListSerializer


    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'department_id',
            openapi.IN_QUERY,
            description="Filter by department ID",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filter by record status (e.g. Approved, Rejected, Pending)",
            type=openapi.TYPE_STRING,
            required=False
        )
    ])

    def get_queryset(self):
        department_id = self.request.GET.get('department_id')
        status = self.request.GET.get('status')
        user = self.request.user

        # Start with records belonging to the user's organization
        qs = self.queryset.filter(organization=user.organization)

        # Filter records based on approval status or role hierarchy
        qs = qs.filter(
            Q(recordrolestatus__isnull=True) |  # No status yet
            Q(recordrolestatus__role__in=user.roles.all(), recordrolestatus__is_approved__in=[True, False]) |  # Approved or Rejected by the user's role
            Q(recordrolestatus__role__next_level__in=user.roles.all(), recordrolestatus__is_approved=True)  # Approved by previous role, pending on the current user's role
        ).distinct()

        # Annotate the status field for easier filtering
        qs = qs.annotate(
            status=Case(
                When(Q(recordrolestatus__role__in=user.roles.all(), recordrolestatus__is_approved=True), then=Value('Approved')),
                When(Q(recordrolestatus__role__in=user.roles.all(), recordrolestatus__is_approved=False), then=Value('Rejected')),
                When(Q(recordrolestatus__role__next_level__in=user.roles.all(), recordrolestatus__is_approved=True), then=Value('Pending')),
                default=Value('Pending')
            )
        )

        # Check if user's roles have previous levels
        if user.roles.filter(prev_level__isnull=False).exists():
            qs = qs.filter(recordrolestatus__isnull=False)

        if department_id:
            qs = qs.filter(department_id=department_id)

        if status in ['Approved', 'Rejected', 'Pending']:
            qs = qs.filter(status=status)

        # qs = qs.prefetch_related('recordrolestatus', 'recordrolestatus__role', 'recordrolestatus__role__prev_level')

        return qs

class RecordRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Record.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecordRetrieveSerializer
        return RecordSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })

        return context



class DocumentCreateAPI(generics.CreateAPIView):
    queryset = RecordDocument.objects.all()
    serializer_class = DocumentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })

        return context


class DocumentDeleteAPI(SoftDeleteMixin, generics.DestroyAPIView):
    queryset = RecordDocument.objects.all()
    serializer_class = DocumentSerializer





class ActionAPIView(APIView):
    serializer_class = ActionSerializer
    def post(self, request, *args, **kwargs):

        user = request.user
        
        serializer = ActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        action = data['action']
        record = data['record']
        comment = data['comment']


        if action == 'approved':
            record.role_level = record.role_level.next_level
            record.save()
        elif action == 'rejected':
            record.role_level = record.role_level.prev_level
            record.save()


        log_instance = RecordLog.objects.create(record=record, action=action, comment=comment, created_by=user)

        RecordRoleStatus.objects.create(
            log=log_instance,
            record=record,
            role=record.role_level,
            is_approved = True if action == 'approved' else False
        )
        message = f'You have {action} this document'
        return Response(
            {
                'status': 200,
                'message': message
            }
        )

