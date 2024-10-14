from django.db import models
from Dms.common.models import CreatorUpdator, TimeStamp


class Organization(models.Model):
    name = models.CharField(max_length=500)
    short_uniq_name = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    

class DepartMent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='org_depts')
    name = models.CharField(max_length=500)
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



class Record(TimeStamp):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    note_sheet_no = models.CharField(max_length=200, null=True, blank=True)
    department = models.ForeignKey(DepartMent, on_delete=models.CASCADE, null=True, blank=True)
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


    role_level = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"PO {self.po_number} - {self.supplier_name}"

    class Meta:
        verbose_name = "Record"
        verbose_name_plural = "Records"





def get_upload_path(instance, file_name):
    return f'RecordDocs/{instance.record.id}/{file_name}'

class RecordDocument(CreatorUpdator):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=get_upload_path)
    file_size = models.FloatField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    




class RecordRoleStatus(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    log = models.ForeignKey('users.RecordLog', on_delete=models.CASCADE, null=True, blank=True)


