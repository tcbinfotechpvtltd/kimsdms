from django.db import models
from Dms.common.models import CreatorUpdator, TimeStamp


class Organization(models.Model):
    name = models.CharField(max_length=500)
    short_uniq_name = models.CharField(max_length=500, null=True, blank=True)
    access_key = models.CharField(max_length=500, null=True, blank=True)
    access_id = models.CharField(max_length=300, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    

class DepartMent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='org_depts')
    name = models.CharField(max_length=500)
    sloc = models.CharField(max_length=50, null=True, blank=True)
    plnt = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    


    


class Roles(TimeStamp):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_roles')
    role_name = models.CharField(max_length=100)
    prev_level = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_level')
    is_active = models.BooleanField(default=True)


    def __str__(self) -> str:
        return f'{self.organization.name}/{self.role_name}'



class Workflow(models.Model):
    work_flow_name = models.CharField(max_length=100, null=True, blank=True)
    work_flow_sloc = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.work_flow_name + " / " + self.work_flow_sloc


class FlowPipeLine(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    wf_prev_level = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='wf_next_level')
    is_active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.workflow) + " / " + str(self.role)



class Record(TimeStamp):
    priority_choices = (
        ('high', 'high'),
        ('med', 'med'),
        ('low', 'low')
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    note_sheet_no = models.CharField(max_length=200, null=True, blank=True)
    priority = models.CharField(choices=priority_choices, default='med')
    # department = models.ForeignKey(DepartMent, on_delete=models.CASCADE, null=True, blank=True)
    department_sloc = models.CharField(max_length=50, null=True, blank=True)
    po_number = models.CharField(max_length=50, verbose_name="PO Number", null=True, blank=True)
    po_date = models.DateField(verbose_name="PO Date", null=True, blank=True)
    vendor_code = models.CharField(max_length=50, verbose_name="Vendor Code", null=True, blank=True)
    supplier_name = models.CharField(max_length=255, verbose_name="Name of the Supplier", null=True, blank=True)
    invoice_date = models.DateField(verbose_name="Invoice Date", null=True, blank=True)
    invoice_number = models.CharField(max_length=50, verbose_name="Invoice Number", null=True, blank=True)
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Invoice Amount", null=True, blank=True)
    total_po_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total PO Amount", null=True, blank=True)
    amount_to_be_paid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount to be Paid", null=True, blank=True)
    
    # Fields for auto-fetched data (placeholders, can be populated based on external SAP integration)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Advance Amount (auto-fetch from SAP)")
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="TDS Amount (auto-fetch from SAP)")


    role_level = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True, related_name='pending_docs')
    approved_by = models.ManyToManyField(Roles, related_name='approved_docs')
    rejected_by = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_docs')
    is_settled = models.BooleanField(default=False)

    note_sheet_url = models.URLField(null=True, blank=True)
    record_name = models.CharField(max_length=300, null=True, blank=True)
    phase = models.PositiveIntegerField(null=True, blank=True)
    data_source = models.CharField(max_length=100, null=True, blank=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"PO {self.po_number} - {self.supplier_name} ({self.id})"

    class Meta:
        verbose_name = "Record"
        verbose_name_plural = "Records"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.id:
            self.note_sheet_no = f'sap-sheet-{self.id}'
            super().save(update_fields=['note_sheet_no']) 




def get_upload_path(instance, file_name):
    return f'RecordDocs/{instance.record.id}/{file_name}'

class RecordDocument(CreatorUpdator):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=get_upload_path)
    file_size = models.FloatField(null=True, blank=True)
    file_name = models.CharField(max_length=200, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    




class RecordRoleStatus(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    log = models.ForeignKey('users.RecordLog', on_delete=models.CASCADE, null=True, blank=True)


class WorkFlowLog(models.Model):
    STATUS = (
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected'),

    )
    flow_pipe_line = models.OneToOneField(FlowPipeLine, on_delete=models.CASCADE)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
