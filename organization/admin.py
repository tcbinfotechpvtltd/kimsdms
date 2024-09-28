from django.contrib import admin

from .models import RecordLog, RecordDocument, Record, Organization, Roles

admin.site.register(RecordLog)
admin.site.register(RecordDocument)
admin.site.register(Record)
admin.site.register(Organization)
admin.site.register(Roles)