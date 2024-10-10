from django.forms import ValidationError
from rest_framework import serializers

from users.serializers import RecordLogSerializer
from .models import Organization, RecordDocument, Roles
from .models import Record, DepartMent
from django.utils import timezone
from users.models import RecordLog

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartMent
        fields = ['id', 'organization', 'name', 'is_active']



class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordDocument
        fields = '__all__'

    
    def create(self, validated_data):
        record = validated_data.get('record')

        user = self.context['request'].user

        instance = super().create(validated_data)

        if instance:
            # creating logs
            RecordLog.objects.create(
                record=record, doc=instance, action='attached', created_by=user
            )

        return instance



class RecordListSerializer(serializers.ModelSerializer):
     status = serializers.CharField()
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
            'status'
        ]

class RecordRetrieveSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        trp = super().to_representation(instance)

        logs_qs = RecordLog.objects.filter(record=instance)

        logs_data = RecordLogSerializer(logs_qs, many=True).data
        trp['activity_logs'] = logs_data

        docs_qs = RecordDocument.objects.filter(record=instance, is_deleted=False)

        docs_data = DocumentSerializer(docs_qs, many=True).data

        trp['docs'] = docs_data

        return trp


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

        instance = super().update(validated_data)

        user = self.context['request'].user

        if instance:
            # creating logs
            RecordLog.objects.create(
                record=instance, action='edited', created_by=user
            )

        return instance




class SapRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = [
            'id',
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
        ]


    def create(self, validated_data):
        organization = Organization.objects.filter(short_uniq_name='sap').first()
        if not organization:
            raise ValidationError(message='No organization object found for SAP')
        
        validated_data['organization'] = organization

        return super().create(validated_data)



class ActionSerializer(serializers.Serializer):
    ACTIONS = (
        ('approved', 'approved'),
        ('rejected', 'rejected')
    )
    action = serializers.ChoiceField(choices=ACTIONS)
    record_id = serializers.IntegerField()
    comment = serializers.CharField(max_length=1000)


    def validate(self, attrs):
        _id = attrs.get('record_id')
        record =  Record.objects.filter(id=_id).first()
        if not record:
            raise ValidationError(message='Record not found with this id')
        attrs['record'] = record
        return attrs

