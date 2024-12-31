import os
import time
from .models import RecordRoleStatus
from .models import Record, DepartMent
import io
from weasyprint import HTML
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from datetime import datetime
from Dms.common.s3_util import S3Storage
from django.conf import settings

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import F
from django.db.models import Value, F, CharField
from django.db.models.functions import Concat



def generate_notesheet_report(record):

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
    'approved_users': []
    }
    approved_users = (
            RecordRoleStatus.objects.filter(
                record=record,
                is_approved=True,
            )
            .annotate(
                first_name=F("log__created_by__first_name"),
                last_name=F("log__created_by__last_name"),
                date=F("log__created_at"),
                photo=F("log__created_by__signature"),
                designation=F("log__created_by__designation"),
                role_name=F("role__role_name"),
                department=F("role__master_department__name"),
            )
            .values(
                "first_name",
                "last_name",
                "date",
                "photo",
                "designation",
                "role_name",
                "department",
            )
        )

    dept_map_approved_users = {}
    wo_dept_map_approved_users = []
    for approved_user in approved_users:
        department = approved_user.get("department")
        if department:
            temp = dept_map_approved_users.get(department, [])
            temp.append(approved_user)
            dept_map_approved_users[department] = temp
        else:
            wo_dept_map_approved_users.append(approved_user)

    context["dept_map_approved_users"] = dept_map_approved_users
    context["wo_dept_map_approved_users"] = wo_dept_map_approved_users
    context["departments"] = list(dept_map_approved_users.keys())
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


    relative_path = f'media/notesheets/{record.id}/notesheet.pdf' 

    s3 = S3Storage()
    res = s3.upload_s3_file(local_source_path=local_path, file_relative_path=relative_path)
    
    try:
        os.unlink(local_path)
    except:
        pass

    absolute_path = os.path.join(settings.MEDIA_URL, str(res).split('media/')[1])

    record.note_sheet_url = absolute_path
    record.save()

    return absolute_path




# def crete_role():
#     from organization.models import DepartMent, Roles
    

#     role_objs = []

#     for dep in DepartMent.objects.all().exclude(sloc='C237'):
#         role_objs.append(
#             Roles(
#             organization_id=1, is_hod=True, parent_role_id=5, store_department=dep, is_active=True, role_name=f"{dep.name} HOD"
#         )
#         )

    
#     if role_objs:
#         Roles.objects.bulk_create(role_objs, ignore_conflicts=True)


