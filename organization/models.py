from django.db import models
from Dms.common.models import CreatorUpdator, TimeStamp


class Organization(models.Model):
    name = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    


class Roles(TimeStamp):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_roles')
    role_name = models.CharField(max_length=100)
    next_lavel = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)


    def __str__(self) -> str:
        return f'{self.organization.name}/{self.role_name}'



class Record(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)

    department = models.CharField(max_length=255, verbose_name="Name of the School / Department")
    po_number = models.CharField(max_length=50, verbose_name="PO Number")
    po_date = models.DateField(verbose_name="PO Date")
    vendor_code = models.CharField(max_length=50, verbose_name="Vendor Code")
    supplier_name = models.CharField(max_length=255, verbose_name="Name of the Supplier")
    invoice_date = models.DateField(verbose_name="Invoice Date")
    invoice_number = models.CharField(max_length=50, verbose_name="Invoice Number")
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Invoice Amount")
    total_po_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total PO Amount")
    amount_to_be_paid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount to be Paid")
    
    # Fields for auto-fetched data (placeholders, can be populated based on external SAP integration)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Advance Amount (auto-fetch from SAP)")
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="TDS Amount (auto-fetch from SAP)")

    def __str__(self):
        return f"PO {self.po_number} - {self.supplier_name}"

    class Meta:
        verbose_name = "Record"
        verbose_name_plural = "Records"





def get_upload_path(instance, file_name):
    return f'PursesOrder/{instance.id}/{file_name}'

class RecordDocument(CreatorUpdator):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=get_upload_path)
    file_size = models.FloatField(null=True, blank=True)
    



class RecordLog(CreatorUpdator, TimeStamp):
    ACTIONS = (
        ('apporved', 'approved'),
        ('rejected', 'rejected'),

    )
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(choices=ACTIONS)
    comment = models.TextField(null=True, blank=True)
    role_level = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True)