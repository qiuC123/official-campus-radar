from django.contrib import admin

from .models import (AnnouncementDiscoveryCandidate, AnnouncementDiscoveryObservation,
                     AnnouncementDiscoveryOrganizationRun,
                     AnnouncementDiscoveryProviderAttempt, AnnouncementDiscoveryRun,
                     AnnouncementFieldEvidence,
                     ApprovedApplicationHost, ApplicationLink,
                     ApplicationProgress, Evidence, FetchRun, RecruitmentPosition,
                     OfficialSource, Organization, OrganizationAlias,
                     PublicationEvent, RecruitmentAnnouncement, RecruitmentBatch,
                     RecruitmentPolicy, RecruitmentPolicyEvent,
                     SourceAdmissionEvent, SourceVersion,
                     UpdateRun, WeChatAccountIdentity)


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
admin.site.register(RecruitmentBatch, AuditReadOnlyAdmin)
admin.site.register(RecruitmentPosition, AuditReadOnlyAdmin)
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
admin.site.register(RecruitmentAnnouncement, AuditReadOnlyAdmin)
admin.site.register(AnnouncementFieldEvidence, AuditReadOnlyAdmin)
admin.site.register(RecruitmentPolicy, AuditReadOnlyAdmin)
admin.site.register(RecruitmentPolicyEvent, AuditReadOnlyAdmin)
admin.site.register(WeChatAccountIdentity)


@admin.register(AnnouncementDiscoveryCandidate)
class AnnouncementDiscoveryCandidateAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "title_hint",
        "source_kind",
        "route_state",
        "provider",
        "state",
        "discovered_at",
    )
    list_filter = ("source_kind", "route_state", "provider", "state")
    search_fields = ("organization__name", "title_hint", "url", "identity_url")
    readonly_fields = (
        "organization",
        "source_kind",
        "url",
        "identity_url",
        "route_state",
        "title_hint",
        "provider",
        "provider_result_id",
        "error_code",
        "announcement",
        "discovered_at",
    )


admin.site.register(AnnouncementDiscoveryRun, AuditReadOnlyAdmin)
admin.site.register(AnnouncementDiscoveryOrganizationRun, AuditReadOnlyAdmin)
admin.site.register(AnnouncementDiscoveryProviderAttempt, AuditReadOnlyAdmin)
admin.site.register(AnnouncementDiscoveryObservation, AuditReadOnlyAdmin)
