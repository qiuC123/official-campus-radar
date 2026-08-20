from django.contrib import admin

from .models import (ApprovedApplicationHost, ApplicationLink,
                     ApplicationProgress, Evidence, FetchRun, NoticePosition,
                     OfficialSource, Organization, OrganizationAlias,
                     PublicationEvent, RecruitmentNotice,
                     SourceAdmissionEvent, SourceVersion, UpdateRun)


class AuditReadOnlyAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SourceAuditAdmin(AuditReadOnlyAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields] if obj else []


admin.site.register(Organization, AuditReadOnlyAdmin)
admin.site.register(OfficialSource, SourceAuditAdmin)
admin.site.register(RecruitmentNotice, AuditReadOnlyAdmin)
admin.site.register(NoticePosition, AuditReadOnlyAdmin)
admin.site.register(ApplicationLink, AuditReadOnlyAdmin)
admin.site.register(ApplicationProgress)
admin.site.register(UpdateRun, AuditReadOnlyAdmin)
admin.site.register(FetchRun, AuditReadOnlyAdmin)
admin.site.register(SourceVersion, AuditReadOnlyAdmin)
admin.site.register(Evidence, AuditReadOnlyAdmin)
admin.site.register(PublicationEvent, AuditReadOnlyAdmin)
admin.site.register(SourceAdmissionEvent, AuditReadOnlyAdmin)
admin.site.register(ApprovedApplicationHost, AuditReadOnlyAdmin)
admin.site.register(OrganizationAlias, AuditReadOnlyAdmin)
