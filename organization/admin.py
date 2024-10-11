from django.contrib import admin

from .models import  RecordDocument, Record, Organization, Roles, DepartMent, RecordRoleStatus

admin.site.register(RecordDocument)
admin.site.register(Record)
admin.site.register(Organization)
admin.site.register(Roles)
admin.site.register(DepartMent)
admin.site.register(RecordRoleStatus)