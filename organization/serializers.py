from rest_framework import serializers
from .models import Roles
from .models import Record
from django.utils import timezone

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'




class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = [
            'id',
            'organization',
            'department',
            'po_number',
            'po_date',
            'vendor_code',
            'supplier_name',
            'invoice_date',
            'invoice_number',
            'invoice_amount',
            'total_po_amount',
            'amount_to_be_paid',
            'advance_amount',
            'tds_amount',
            'updated_at'
        ]

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        updated_at = timezone.now()
        validated_data['updated_at'] = updated_at

        return super().update(validated_data)