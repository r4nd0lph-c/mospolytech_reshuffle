# TODO: add action "change activity flag" for selected SubjectAdmin & TaskAdmin
# TODO: add filter by "position" field for TaskAdmin
# TODO: add highlighting for uncompleted Parts and Tasks

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db.models import Q
from reshuffle.settings import PROJECT_NAME
from main.views import Auth, logout_user
from main.models import *

# UTILS -------------------------------------------------------------------------------------------------------------- #
admin.site.site_title = PROJECT_NAME
admin.site.site_header = PROJECT_NAME.upper()
admin.site.index_title = _("Administration")

admin.site.login = Auth.as_view()
admin.site.logout = logout_user


class AdministrationEntry(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


def get_accesses(groups):
    accesses = []
    for g in groups:
        accesses += [a.subject.id for a in Access.objects.filter(group=g)]
    return accesses


# CUSTOM FILTERS ----------------------------------------------------------------------------------------------------- #
class InstAvailableFilter(admin.SimpleListFilter):
    title = _("Instruction available")
    parameter_name = "is_inst_available__exact"

    def lookups(self, request, model_admin):
        return [
            ("1", _("Yes")),
            ("0", _("No")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(~Q(inst_content__exact=""))
        if self.value() == "0":
            return queryset.filter(inst_content__exact="")


# MAIN --------------------------------------------------------------------------------------------------------------- #
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (_("Subject"), {
            "fields": ("sbj_title", "is_active",)
        }),
        (_("Additional options"), {
            "classes": ("collapse",),
            "fields": ("case_genitive", "case_dative", "case_accusative", "case_instrumental", "case_prepositional",)
        }),
        (_("Instruction"), {
            "fields": ("inst_content",)
        }),
    )
    list_display = ("id", "sbj_title", "inst_available", "is_active", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("id",)
    list_filter = (InstAvailableFilter, "is_active",)

    def inst_available(self, obj: "Subject"):
        if obj.inst_content:
            return True
        return False

    inst_available.boolean = True
    inst_available.short_description = _("Instruction")

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    fieldsets = (
        (_("Subject"), {
            "fields": ("subject",)
        }),
        (_("Main options"), {
            "fields": ("title", "answer_type", "task_count", "total_difficulty",)
        }),
        (_("Instruction"), {
            "fields": ("inst_content",)
        }),
    )
    list_display = (
        "id", "subject", "title", "cell_count", "answer_type", "task_count",
        "total_difficulty", "inst_available", "created", "updated",
    )
    list_display_links = ("id",)
    ordering = ("subject", "title")
    list_filter = (("subject", admin.RelatedOnlyFieldListFilter), InstAvailableFilter,)

    def cell_count(self, obj: "Part"):
        return ceil(obj.task_count / Part.CAPACITIES[obj.answer_type])

    cell_count.short_description = _("Cells")

    def inst_available(self, obj: "Part"):
        if obj.inst_content:
            return True
        return False

    inst_available.boolean = True
    inst_available.short_description = _("Instruction")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = request.user.groups.all()
        if request.user.is_superuser or not groups.exists():
            return qs
        return qs.filter(subject__id__in=get_accesses(groups))

    def get_form(self, request, obj: "Part" = None, **kwargs):
        form = super(PartAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["subject"].widget.can_change_related = False
        form.base_fields["subject"].widget.can_add_related = False
        form.base_fields["subject"].widget.can_view_related = False
        groups = request.user.groups.all()
        if not request.user.is_superuser or groups.exists():
            form.base_fields["subject"].queryset = Subject.objects.filter(id__in=get_accesses(groups))
        return form

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js", "admin/js/model_part_validation.js",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "part", "position", "difficulty", "is_active", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("part__subject", "part", "position", "difficulty", "-is_active",)
    list_filter = (("part__subject", admin.RelatedOnlyFieldListFilter), "difficulty", "is_active",)
    search_fields = ("id",)
    search_help_text = _("The search is performed by task ID")

    def pretty_content(self, obj: "Task"):
        return mark_safe(f"<div class='td_content'> {obj.content} </div>")

    pretty_content.short_description = Task._meta.get_field("content").verbose_name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = request.user.groups.all()
        if request.user.is_superuser or not groups.exists():
            return qs
        return qs.filter(part__subject__id__in=get_accesses(groups))

    def get_form(self, request, obj: "Task" = None, **kwargs):
        form = super(TaskAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["part"].widget.can_change_related = False
        form.base_fields["part"].widget.can_add_related = False
        form.base_fields["part"].widget.can_view_related = False
        groups = request.user.groups.all()
        if not request.user.is_superuser or groups.exists():
            form.base_fields["part"].queryset = Part.objects.filter(subject__id__in=get_accesses(groups))
        return form

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js", "admin/js/model_task_validation.js",)


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "task", "is_answer", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("task", "-is_answer",)
    list_filter = (("task__part__subject", admin.RelatedOnlyFieldListFilter), "is_answer",)
    autocomplete_fields = ("task",)
    search_fields = ("task__id",)
    search_help_text = _("The search is performed by task ID")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = request.user.groups.all()
        if request.user.is_superuser or not groups.exists():
            return qs
        return qs.filter(task__part__subject__id__in=get_accesses(groups))

    def get_form(self, request, obj: "Option" = None, **kwargs):
        form = super(OptionAdmin, self).get_form(request, obj, **kwargs)
        groups = request.user.groups.all()
        if not request.user.is_superuser or groups.exists():
            form.base_fields["task"].queryset = Task.objects.filter(part__subject__id__in=get_accesses(groups))
        return form

    def pretty_content(self, obj: "Option"):
        return mark_safe(f"<div class='td_content'> {obj.content} </div>")

    pretty_content.short_description = Option._meta.get_field("content").verbose_name

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js",)


@admin.register(DocHeader)
class DocHeaderAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "is_active", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("-is_active", "-updated",)

    def pretty_content(self, obj: "DocHeader"):
        return mark_safe(f"<div class='td_content'> {obj.content} </div>")

    pretty_content.short_description = DocHeader._meta.get_field("content").verbose_name

    def delete_queryset(self, request, qs):
        if qs.filter(is_active=True):
            qs_remaining = DocHeader.objects.order_by("-updated").exclude(id__in=qs.values("id"))
            if qs_remaining:
                obj = qs_remaining[0]
                obj.is_active = True
                obj.save()
        qs.delete()

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js",)


# ADMINISTRATION ----------------------------------------------------------------------------------------------------- #
@admin.register(LogEntry)
class LogEntryAdmin(AdministrationEntry):
    readonly_fields = ("action_time",)
    list_display = ("id", "__str__", "content_type", "username", "action_time",)
    list_display_links = ("id",)
    date_hierarchy = "action_time"
    list_filter = (("user", admin.RelatedOnlyFieldListFilter), ("content_type", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("object_repr",)
    search_help_text = _("The search is performed by object representation")

    def username(self, obj: "LogEntry"):
        return obj.user.get_full_name() if obj.user.get_full_name() else obj.user.username

    username.short_description = LogEntry._meta.get_field("user").verbose_name

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ObjectStorageEntry)
class ObjectStorageEntryAdmin(AdministrationEntry):
    list_display = ("id", "subject", "date", "amount", "username", "created", "download_button",)
    list_display_links = ("id",)
    date_hierarchy = "created"
    ordering = ("-created",)
    list_filter = (("subject", admin.RelatedOnlyFieldListFilter), ("user", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("prefix",)
    search_help_text = _("The search is performed by prefix")

    def username(self, obj: "ObjectStorageEntry"):
        return obj.user.get_full_name() if obj.user.get_full_name() else obj.user.username

    username.short_description = ObjectStorageEntry._meta.get_field("user").verbose_name

    def download_button(self, obj: "ObjectStorageEntry"):
        btn = """
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708z"/>
            </svg>
        """
        return mark_safe(f"<a href='{reverse_lazy("download_archive", kwargs={"prefix": obj.prefix})}'> {btn} </a>")

    download_button.short_description = _("Download")

    def delete_queryset(self, request, qs):
        mc = MinioClient()
        for obj in qs:
            mc.delete_object(obj.prefix)
        qs.delete()


@admin.register(VerifiedWorkEntry)
class VerifiedWorkEntryAdmin(AdministrationEntry):
    list_display = ("id", "archive", "unique_key", "score", "username", "created",)
    list_display_links = ("id",)
    date_hierarchy = "created"
    ordering = ("-created",)
    list_filter = (("archive", admin.RelatedOnlyFieldListFilter), ("user", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("unique_key",)
    search_help_text = _("The search is performed by unique key")

    def username(self, obj: "VerifiedWorkEntry"):
        return obj.user.get_full_name() if obj.user.get_full_name() else obj.user.username

    username.short_description = VerifiedWorkEntry._meta.get_field("user").verbose_name

    def delete_queryset(self, request, qs):
        mc = MinioClient()
        for obj in qs:
            mc.delete_object(obj.alias)
        qs.delete()

    class Media:
        js = ("admin/js/model_verified_work_entry_modification.js",)


# AUTHENTICATION AND AUTHORIZATION ----------------------------------------------------------------------------------- #
@admin.register(Access)
class AccessAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "subject", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("group", "subject",)
    list_filter = (("group", admin.RelatedOnlyFieldListFilter), ("subject", admin.RelatedOnlyFieldListFilter),)
