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
from django.db.models import Q, Case, When, Value, F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import io
from django.http import HttpResponse
from jinja2 import Template
from weasyprint import HTML
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from datetime import datetime

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
        comment = data.get('comment')

        doc = None


        if action == 'approved':
            if hasattr(record.role_level, 'next_level'):
                record.role_level = record.role_level.next_level
                record.save()
        elif action == 'rejected':
            if hasattr(record.role_level, 'prev_level'):
                record.role_level = record.role_level.prev_level
                record.save()
        
        elif action == 'attached':
            file = data.get('file')
            if file:
                doc = RecordDocument.objects.create(record=record, file=file, created_by=user)


        log_instance = RecordLog.objects.create(record=record, action=action, comment=comment, created_by=user, doc=doc)

        if action in ['approved', 'rejected']:
            recordRoleStatusObj = RecordRoleStatus.objects.filter(record=record, role=record.role_level).first()
            if recordRoleStatusObj:
                recordRoleStatusObj.is_approved = True if action == 'approved' else False
                recordRoleStatusObj.save()
            
            else:
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





# def generate_html_to_pdf(request):
#     # Sample data to be passed to the HTML template
#     context = {
#         'title': 'Invoice',
#         'items': [
#             {'name': 'Item 1', 'price': 100},
#             {'name': 'Item 2', 'price': 200},
#             {'name': 'Item 3', 'price': 300},
#         ],
#         'total': 600,
#     }

#     # Define your HTML template (this can also be loaded from a file)
#     html_template = """
#     <html>
#     <head>
#         <style>
#             body { font-family: Arial, sans-serif; }
#             table { width: 100%; border-collapse: collapse; }
#             th, td { padding: 8px 12px; border: 1px solid #ddd; }
#             th { background-color: #f4f4f4; }
#         </style>
#     </head>
#     <body>
#         <h1>{{ title }}</h1>
#         <table>
#             <thead>
#                 <tr>
#                     <th>Item</th>
#                     <th>Price</th>
#                 </tr>
#             </thead>
#             <tbody>
#                 {% for item in items %}
#                 <tr>
#                     <td>{{ item.name }}</td>
#                     <td>{{ item.price }}</td>
#                 </tr>
#                 {% endfor %}
#             </tbody>
#             <tfoot>
#                 <tr>
#                     <th>Total</th>
#                     <th>{{ total }}</th>
#                 </tr>
#             </tfoot>
#         </table>
#     </body>
#     </html>
#     """

#     # Use Jinja2 to render the template with context
#     template = Template(html_template)
#     rendered_html = template.render(context)

#     # Convert rendered HTML to PDF
#     pdf_file = io.BytesIO()  # Use in-memory file
#     HTML(string=rendered_html).write_pdf(pdf_file)

#     # Move the buffer's position back to the beginning
#     pdf_file.seek(0)

#     # Create the HTTP response with the PDF content
#     response = HttpResponse(pdf_file, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="document.pdf"'

#     return response


@api_view(['POST'])
def generate_report_pdf(request):
    record_id = request.data.get('record_id')

    try:
        record = Record.objects.get(id=record_id)
    except:
        return Response({'statusCode': 404, 'message': 'Record not found'})
    


    context = {
    'note_sheet_no': record.note_sheet_no,
    "department": record.department.name if record.department else '',
    "po_number": record.po_number,
    "po_date": record.po_date,
    "vendor_code": record.vendor_code,
    "supplier_name": record.supplier_name,
    "invoice_date": record.invoice_date,
    "invoice_number": record.invoice_number,
    "invoice_amount": record.invoice_amount,
    "total_po_amount": record.total_po_amount,
    "amount_to_be_paid": record.amount_to_be_paid,
    "advance_amount": record.advance_amount,
    "tds_amount": record.tds_amount,
    'curr_date': str(datetime.now().date()),
    'approved_users': RecordRoleStatus.objects.filter(record=record, is_approved=True).annotate(
        first_name = F('log__created_by__first_name'),
        last_name = F('log__created_by__last_name'),
        date = F('log__created_at')
    ).values(
        'first_name', 'last_name', 'date'
    )
    }

    print(context)

    # Load the HTML template from a file using render_to_string
    rendered_html = render_to_string('report.html', context)

    # Convert rendered HTML to PDF
    pdf_file = io.BytesIO()  # Use in-memory file
    HTML(string=rendered_html).write_pdf(pdf_file)

    # Move the buffer's position back to the beginning
    pdf_file.seek(0)

    # Create the HTTP response with the PDF content
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="document.pdf"'

    return response


