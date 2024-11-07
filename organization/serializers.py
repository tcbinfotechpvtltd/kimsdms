from django.forms import ValidationError
from rest_framework import serializers

from users.serializers import RecordLogSerializer
from .models import Organization, RecordDocument, Roles
from .models import Record, DepartMent
from django.utils import timezone
from users.models import RecordLog, User

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartMent
        fields = ['id', 'organization', 'name', 'sloc', 'plnt', 'is_active']



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


class UserBasicSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name','photo',"contact"]

    def get_photo(self, obj):
            # This will return the URL without any additional prefix if set up correctly
            return obj.photo.name if obj.photo else None
class DocBasicSerializer(serializers.ModelSerializer):
     class Meta:
        model = RecordDocument
        fields = ['id', 'file_name', 'file']

class RecordListSerializer(serializers.ModelSerializer):
    status = serializers.CharField()
    department_name = serializers.CharField()
    at_initial_role = serializers.BooleanField()
    duration = serializers.DurationField()
    class Meta:
        model = Record
        fields = [
            'id',
            'record_name',
            'note_sheet_no',
            'organization',
            'department_sloc',
            'department_name',
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
            'status',
            'priority',
            'at_initial_role',
            'note_sheet_url',
            'duration',
            'phase',
            'data_source'
        ]


    def to_representation(self, instance):
        rp =  super().to_representation(instance)
        rp['priority'] = 'medium' if instance.priority == 'med' else instance.priority

        last_log = instance.logs.filter(action__in=['approved', 'rejected']).last()

        last_action = last_log.action if last_log else ''
        user_info = UserBasicSerializer(last_log.created_by).data if last_log and last_log.created_by else {}

        docs = DocBasicSerializer(instance.documents.all(), many=True).data

        rp['last_action'] = last_action
        rp['last_action_done_by'] = user_info
        rp['docs'] = docs

        return rp
    


class RecordRetrieveSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField()
    status = serializers.CharField()

    class Meta:
        model = Record
        fields = [
            'id',
            'organization',
            'note_sheet_no',
            'department_sloc',
            'department_name',
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
            'updated_at',
            'status'
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
            'note_sheet_no',
            'department_sloc',
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
            'note_sheet_no',
            'department_sloc',
            'record_name',
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
            'phase',
            'data_source'
        ]


    def create(self, validated_data):
        organization = Organization.objects.filter(short_uniq_name='sap').first()
        if not organization:
            raise ValidationError(message='No organization object found for SAP')
        
        role = Roles.objects.filter(organization=organization, prev_level__isnull=True).first()

        validated_data['organization'] = organization
        validated_data['role_level'] = role


        return super().create(validated_data)



class ActionSerializer(serializers.Serializer):
    ACTIONS = (
        ('approved', 'approved'),
        ('rejected', 'rejected'),
        ('commented', 'commented'),
        ('attached', 'attached')
    )
    action = serializers.ChoiceField(choices=ACTIONS)
    record_id = serializers.IntegerField()
    
    # Comment is optional and can be blank or null
    comment = serializers.CharField(
        max_length=1000, 
        required=False, 
        allow_blank=True,  # Allows an empty string
        allow_null=True    # Allows null values (None)
    )
    
    # File is optional
    file = serializers.FileField(required=False, allow_null=True)

    def validate(self, data):
        """
        Custom validation if certain actions require comment or file.
        For example, 'commented' action must have a comment.
        """
        action = data.get('action')

        if action == 'commented' and not data.get('comment'):
            raise serializers.ValidationError({"comment": "Comment is required for the 'commented' action."})

        if action == 'attached' and not data.get('file'):
            raise serializers.ValidationError({"file": "File is required for the 'attached' action."})
        

        _id = data.get('record_id')
        record =  Record.objects.filter(id=_id).first()
        if not record:
            raise ValidationError(message='Record not found with this id')
        data['record'] = record


        return data
       

