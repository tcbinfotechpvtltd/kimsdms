import os
import time
from django.forms import ValidationError
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from Dms.common.mixins import SoftDeleteMixin
from organization.permissions import authenticate_access_key
from organization.utils import generate_notesheet_report
from users.models import RecordLog
from users.serializers import RecordLogSerializer
from .models import FlowPipeLine, RecordDocument, RecordRoleStatus, Roles
from .serializers import ActionSerializer, DocumentSerializer, RecordListSerializer, RecordRetrieveSerializer, RolesSerializer, SapRecordSerializer, UpdateRecordSerializer
from .models import Record, DepartMent
from .serializers import RecordSerializer, DepartmentSerializer
from django_filters import rest_framework as filters
from django.db.models import Q, Case, When, Value, F, Subquery, OuterRef, Count, Exists, IntegerField, DateTimeField, BooleanField, DurationField, ExpressionWrapper, CharField
from django.db.models.functions import Concat
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import io
from django.http import HttpResponse
from jinja2 import Template
from weasyprint import HTML
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from datetime import datetime
from Dms.common.s3_util import S3Storage
from django.conf import settings

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.permissions import AllowAny
from django.utils import timezone



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

class RecordUpdateView(generics.UpdateAPIView):
    queryset = Record.objects.all()
    serializer_class = UpdateRecordSerializer

class SapRecordCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = Record.objects.all()
    serializer_class = SapRecordSerializer


    def create(self, request, *args, **kwargs):
        is_success, resp = authenticate_access_key(request)
        if is_success:
            return super().create(request, *args, **kwargs)
        return resp



class RecordListView(generics.ListAPIView):
    queryset = Record.objects.all().prefetch_related('logs', 'documents')
    serializer_class = RecordListSerializer


    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'department_sloc',
            openapi.IN_QUERY,
            description="Filter by department Slock",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filter by record status (e.g. Approved, Rejected, Pending, Settled)",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'priority',
            openapi.IN_QUERY,
            description="Filter by record priority (e.g. low, mid, high)",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'search',
            openapi.IN_QUERY,
            description="Search by notesheet no",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'id',
            openapi.IN_QUERY,
            description="filter by id",
            type=openapi.TYPE_INTEGER,
            required=False
        )
    ])

    # def get_queryset(self):
    #     department_sloc = self.request.GET.get('department_sloc')
    #     status = self.request.GET.get('status')
    #     priority = self.request.GET.get('priority')
    #     search = self.request.GET.get('search')
    #     _id = self.request.GET.get('id')
    #     order_by = self.request.GET.get('order_by')


    #     user = self.request.user

    #     assigned_roles = user.roles.all()

    #     all_roles = Roles.objects.filter(organization=user.organization)

    #     last_role = all_roles.filter(next_level__isnull=True).first()

    #     last_role_users = last_role.role_users.all()

    #     qs = self.queryset.annotate(
    #         approved_roles_count=Count(
    #             'approved_by',
    #             filter=Q(approved_by__in=all_roles),
    #             distinct=True
    #         ),
    #         all_roles_count=Value(len(all_roles), output_field=IntegerField()),
    #         department_name=Subquery(
    #             DepartMent.objects.filter(sloc=OuterRef('department_sloc')).values('name')[:1]
    #             )
    #     )

    #     qs = qs.annotate(
    #         is_pending=Exists(
    #             qs.filter(role_level__in=assigned_roles, id=(OuterRef('id')))
    #                 .exclude(approved_by__in=assigned_roles, id=(OuterRef('id')))
    #                 .exclude(rejected_by__in=assigned_roles, id=(OuterRef('id')))
    #         ),
    #         is_approved=Exists(
    #             qs.filter(approved_by__in=assigned_roles, id=(OuterRef('id'))).
    #                 exclude(
    #                 Q(approved_roles_count=F('all_roles_count'), id=(OuterRef('id')))
    #             )
    #         ),
    #         is_rejected=Exists(
    #             qs.filter(rejected_by__isnull=False, id=(OuterRef('id')))
    #         ),
    #         )

    #     qs = qs.annotate(
    #         status = Case(
    #             When(approved_roles_count=F('all_roles_count'), then=Value("Settled")),
    #             When(is_pending=True, then=Value('Pending')),
    #             When(is_approved=True, then=Value('Approved')),
    #             When(is_rejected=True, then=Value('Rejected')),
    #         )
    #     ).filter(
    #         status__isnull=False
    #         )

    #     qs = qs.annotate(
    #         duration=Case(
    #             When(
    #                 Q(status='Pending'),
    #                 then=ExpressionWrapper(
    #                     timezone.now() -
    #                     ExpressionWrapper(
    #                         Case(
    #                             When(
    #                                 Q(logs__isnull=False),
    #                                 then=RecordLog.objects.filter(
    #                                 record_id=OuterRef('id'),
    #                                 action='approved'
    #                                 ).order_by('-created_at').values('created_at')[:1]
    #                                 ),
    #                             default=F('created_at'),
    #                             output_field=DateTimeField()
    #                         ),
    #                     output_field=DateTimeField(),
    #                     ),
    #                     output_field=DurationField()
    #                 )
    #             ),


    #             When(
    #                 Q(status='Approved'),
    #                 then=ExpressionWrapper(
    #                 timezone.now() -
    #                 Subquery(
    #                     RecordLog.objects.filter(
    #                         record_id=OuterRef('id'),
    #                         created_by=user,
    #                         action='approved'
    #                     ).order_by('-created_at').values('created_at')[:1]
    #             ),
    #             output_field=DurationField()
    #             )
    #             ),
    #             When(
    #                 Q(status='Rejected'),
    #                 then=ExpressionWrapper(
    #                 timezone.now() -
    #                 Subquery(
    #                     RecordLog.objects.filter(
    #                         record_id=OuterRef('id'),
    #                         created_by=user,
    #                         action='rejected'
    #                     ).order_by('-created_at').values('created_at')[:1]
    #             ),
    #             output_field=DurationField()
    #             )
    #             ),
    #             When(
    #                 Q(status='Settled'),
    #                 then=ExpressionWrapper(
    #                 timezone.now() -
    #                 Subquery(
    #                     RecordLog.objects.filter(
    #                         record_id=OuterRef('id'),
    #                         created_by__in=last_role_users,
    #                         action='approved'
    #                     ).order_by('-created_at').values('created_at')[:1]
    #             ),
    #             output_field=DurationField()
    #             )
    #             ),

    #             default=None,
    #             output_field=DurationField()
    #         )
    #     )

    #     qs = qs.annotate(
    #         at_initial_role=Case(
    #             When(role_level__prev_level__isnull=True, then=Value(True, BooleanField())),
    #             default=Value(False, BooleanField())
    #         )
    #     )

    #     if _id:
    #         qs = qs.filter(id=_id)
    #         return qs

    #     if department_sloc:
    #         qs = qs.filter(department_sloc=department_sloc)

    #     if status:
    #         qs = qs.filter(
    #             status=status
    #         )

    #     if priority:
    #         if priority == 'medium':
    #             priority = 'med'
    #         qs = qs.filter(priority=priority, status='Pending')

    #     if search:
    #         qs = qs.filter(Q(note_sheet_no__icontains=search))


    #     if order_by:
    #         if order_by in ['duration', '-duration']:
    #             qs =  qs.order_by(order_by)

    #     return qs






    def get_queryset(self):
        department_sloc = self.request.GET.get('department_sloc')
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        search = self.request.GET.get('search')
        _id = self.request.GET.get('id')
        order_by = self.request.GET.get('order_by')


        user = self.request.user

        assigned_roles = user.roles.all()

        # all_roles = Roles.objects.filter(organization=user.organization)

        # last_role = all_roles.filter(next_level__isnull=True).first()

        # last_role_users = last_role.role_users.all()

        qs = self.queryset.annotate(
            # approved_roles_count=Count(
            #     'approved_by',
            #     filter=Q(approved_by__in=all_roles),
            #     distinct=True
            # ),
            # all_roles_count=Value(len(all_roles), output_field=IntegerField()),
            department_name=Subquery(
                DepartMent.objects.filter(sloc=OuterRef('department_sloc')).values('name')[:1]
                )
        )

        qs = qs.annotate(
            is_pending=Exists(
                qs.filter(role_level__in=assigned_roles, id=(OuterRef('id')))
                    .exclude(approved_by__in=assigned_roles, id=(OuterRef('id')))
                    .exclude(rejected_by__in=assigned_roles, id=(OuterRef('id')))
            ),
            is_approved=Exists(
                qs.filter(approved_by__in=assigned_roles, id=(OuterRef('id'))).
                    exclude(
                    Q(is_settled=True, id=(OuterRef('id')))
                )
            ),
            is_rejected=Exists(
                qs.filter(rejected_by__isnull=False, id=(OuterRef('id')))
            ),
            )

        qs = qs.annotate(
            status = Case(
                When(is_settled=True, then=Value("Settled")),
                When(is_pending=True, then=Value('Pending')),
                When(is_approved=True, then=Value('Approved')),
                When(is_rejected=True, then=Value('Rejected')),
            )
        ).filter(
            status__isnull=False
            )

        qs = qs.annotate(
            duration=Case(
                When(
                    Q(status='Pending'),
                    then=ExpressionWrapper(
                        timezone.now() -
                        ExpressionWrapper(
                            Case(
                                When(
                                    Q(logs__isnull=False),
                                    then=RecordLog.objects.filter(
                                    record_id=OuterRef('id'),
                                    action='approved'
                                    ).order_by('-created_at').values('created_at')[:1]
                                    ),
                                default=F('created_at'),
                                output_field=DateTimeField()
                            ),
                        output_field=DateTimeField(),
                        ),
                        output_field=DurationField()
                    )
                ),


                When(
                    Q(status='Approved'),
                    then=ExpressionWrapper(
                    timezone.now() -
                    Subquery(
                        RecordLog.objects.filter(
                            record_id=OuterRef('id'),
                            created_by=user,
                            action='approved'
                        ).order_by('-created_at').values('created_at')[:1]
                ),
                output_field=DurationField()
                )
                ),
                When(
                    Q(status='Rejected'),
                    then=ExpressionWrapper(
                    timezone.now() -
                    Subquery(
                        RecordLog.objects.filter(
                            record_id=OuterRef('id'),
                            created_by=user,
                            action='rejected'
                        ).order_by('-created_at').values('created_at')[:1]
                ),
                output_field=DurationField()
                )
                ),
                When(
                    Q(status='Settled'),
                    then=ExpressionWrapper(
                    timezone.now() -
                    Subquery(
                        RecordLog.objects.filter(
                            record_id=OuterRef('id'),
                            # created_by__in=last_role_users,
                            action='approved'
                        ).order_by('-created_at').values('created_at')[:1]
                ),
                output_field=DurationField()
                )
                ),

                default=None,
                output_field=DurationField()
            )
        )

        qs = qs.annotate(
            at_initial_role=Case(
                When(role_level__prev_level__isnull=True, then=Value(True, BooleanField())),
                default=Value(False, BooleanField())
            )
        )

        if _id:
            qs = qs.filter(id=_id)
            return qs

        if department_sloc:
            qs = qs.filter(department_sloc=department_sloc)

        if status:
            qs = qs.filter(
                status=status
            )

        if priority:
            if priority == 'medium':
                priority = 'med'
            qs = qs.filter(priority=priority, status='Pending')

        if search:
            qs = qs.filter(Q(note_sheet_no__icontains=search))




        qs = qs.order_by('id').distinct('id')

        if order_by:
            if order_by in ['duration', '-duration']:
                qs =  qs.order_by( 'id', order_by)

        return qs







    def list(self, request, *args, **kwargs):
        serialized_data = RecordListSerializer(self.get_queryset(), many=True).data

        is_statistics = request.GET.get('is_statistics')
        status = self.request.GET.get('status')
        _id = self.request.GET.get('id')
        # priority = self.request.GET.get('priority')
        # search = self.request.GET.get('search')


        # if status in ['Approved', 'Rejected', 'Pending', 'Settled']:
        #     serialized_data = [data for data in serialized_data if data['status'] == status]

        # if priority:
        #     serialized_data = [data for data in serialized_data if data['status'] == "Pending" and data['priority'] == 'high']

        # if search:
        #    serialized_data = [data for data in serialized_data if search in data['note_sheet_no']]

        if _id:
            if len(serialized_data) > 0:
                _data = serialized_data[0]
                logs_qs = RecordLog.objects.filter(record_id=_id)
                logs_data = RecordLogSerializer(logs_qs, many=True).data
                _data['activity_logs'] = logs_data
                return Response(_data)

            return Response({})

        if is_statistics:
            status_options = ['Approved', 'Rejected', 'Pending', 'Settled']
            priority_counts = {'High-Priority': 0}

            status_count_dict = {status: 0 for status in status_options}

            for item in serialized_data:
                status = item.get('status')
                if status in status_count_dict:
                    status_count_dict[status] += 1

                if item.get('priority') == 'high' and item.get('status') =="Pending":
                    priority_counts['High-Priority'] += 1

            response_data = {
                'status_counts': status_count_dict,
                'high_priority_count': priority_counts['High-Priority'],
            }
        else:
            response_data = serialized_data

        return Response(response_data)




class RecordRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Record.objects.all().annotate(
        department_name=Subquery(
                DepartMent.objects.filter(sloc=OuterRef('department_sloc')).values('name')[:1]
                )
    )

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

        approve_reject_by = None

        # if action == 'approved':
        #     if record.role_level:
        #         approve_reject_by = record.role_level
        #         if hasattr(record.role_level, 'next_level'):
        #             record.role_level = record.role_level.next_level
        #         record.approved_by.add(approve_reject_by)
        #         record.rejected_by = None
        #         record.save()

        if action == 'approved':
            if record.role_level:
                approve_reject_by = record.role_level
                pipeline = FlowPipeLine.objects.filter(workflow=record.workflow, role=record.role_level).first()
                if pipeline and hasattr(pipeline, 'wf_next_level'):
                    next_pipe_line = pipeline.wf_next_level
                    next_role = next_pipe_line.role
                    record.role_level = next_role
                record.approved_by.add(approve_reject_by)
                record.rejected_by = None
                record.save()

        # elif action == 'rejected':
        #     if record.role_level:
        #         record.approved_by.clear() # clearing all approves
        #         approve_reject_by = record.role_level
        #         if hasattr(record.role_level, 'prev_level'):
        #             record.role_level = Roles.objects.filter(organization=user.organization, prev_level__isnull=True).first()  # shifting it to initial role
        #         record.rejected_by = approve_reject_by
        #         record.save()

        elif action == 'rejected':
            if record.role_level:
                record.approved_by.clear() # clearing all approves
                approve_reject_by = record.role_level
                pipeline = FlowPipeLine.objects.filter(workflow=record.workflow, role=record.role_level).first()
                if pipeline and hasattr(pipeline, 'wf_prev_level'):
                    initial_pipeline = FlowPipeLine.objects.filter(workflow=record.workflow, wf_prev_level__isnull=True).first()
                    record.role_level = initial_pipeline.role # shifting it to initial role
                record.rejected_by = approve_reject_by
                record.save()


        if action == 'approved':
            workflow_roles = set(
                FlowPipeLine.objects.filter(workflow=record.workflow).values_list('role', flat=True)
            )
            approved_roles = set(record.approved_by.all().values_list('id', flat=True))

            if workflow_roles == approved_roles:
                record.is_settled = True
                record.save()



        elif action == 'attached':
            file = data.get('file')
            if file:
                file_name = file.name
                doc = RecordDocument.objects.create(record=record, file=file, created_by=user, file_name=file_name)
                local_path = doc.file.path
                relative_path = 'media/' + doc.file.url.split('media/')[1]
                # print(local_path, relative_path)
                s3 = S3Storage()
                res = s3.upload_s3_file(local_source_path=local_path, file_relative_path=relative_path)

                try:
                    os.unlink(local_path)
                except: pass



        log_instance = RecordLog.objects.create(record=record, action=action, comment=comment, created_by=user, doc=doc)

        if action in ['approved', 'rejected']:
            recordRoleStatusObj = RecordRoleStatus.objects.filter(record=record, role=approve_reject_by).first()
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


        if action == 'approved':
            path = generate_notesheet_report(record)

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

    department_obj = DepartMent.objects.filter(sloc=record.department_sloc).first()

    if department_obj:
        department = department_obj.name
    else: department = ''

    context = {
    'note_sheet_no': record.note_sheet_no,
    "department": department,
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
        date = F('log__created_at'),
        photo=Concat(
        Value(settings.MEDIA_URL),
        F('log__created_by__signature'),
        output_field=CharField()
        ),
        role_name = F('role__role_name')
    ).values(
        'first_name', 'last_name', 'date', 'photo', 'role_name'
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



    ##############################################
    file_name = f'notesheets/{time.time()}.pdf'

    # Save to S3 (default_storage refers to the storage backend, which is S3 in your case)
    content = ContentFile(pdf_file.read())  # Create a ContentFile from the BytesIO
    file_url = default_storage.save(file_name, content)

    # You now have the URL for the saved PDF
    print("File uploaded to S3:", file_url)



    local_path = os.path.join(settings.PROJECT_ROOT, 'media', file_name)


    relative_path = f'media/notesheets/{record_id}/notesheet.pdf'

    s3 = S3Storage()
    res = s3.upload_s3_file(local_source_path=local_path, file_relative_path=relative_path)

    try:
        os.unlink(local_path)
    except:
        pass

    absolute_path = os.path.join(settings.MEDIA_URL, str(res).split('media/')[1])

    record.note_sheet_url = absolute_path
    record.save()

    response = {
        "url": absolute_path
    }
    return Response(response)

    ###############################################

    # # Create the HTTP response with the PDF content
    # response = HttpResponse(pdf_file, content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename="document.pdf"'

    # return response




