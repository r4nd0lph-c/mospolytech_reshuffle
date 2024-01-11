# TODO: add action "change activity flag" for selected SubjectAdmin & TaskAdmin
# TODO: add filter by "position" field for TaskAdmin

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.db.models import Q
from reshuffle.settings import PROJECT_NAME
from main.models import *

# UTILS -------------------------------------------------------------------------------------------------------------- #
admin.site.site_title = PROJECT_NAME
admin.site.site_header = PROJECT_NAME
admin.site.index_title = _("Administration")


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


# TESTING MATERIALS -------------------------------------------------------------------------------------------------- #
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
            "fields": ("inst_title", "inst_content",)
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

    def get_form(self, request, obj: "Part" = None, **kwargs):
        form = super(PartAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["subject"].widget.can_change_related = False
        form.base_fields["subject"].widget.can_add_related = False
        form.base_fields["subject"].widget.can_view_related = False
        return form

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js", "admin/js/model_part_validation.js")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "part", "position", "difficulty", "is_active", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("part", "position", "difficulty", "-is_active",)
    list_filter = (("part__subject", admin.RelatedOnlyFieldListFilter), "difficulty", "is_active",)

    def pretty_content(self, obj: "Task"):
        return mark_safe(f"<div class='td_content'> {obj.content} </div>")

    pretty_content.short_description = DocHeader._meta.get_field("content").verbose_name

    def get_form(self, request, obj: "Task" = None, **kwargs):
        form = super(TaskAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["part"].widget.can_change_related = False
        form.base_fields["part"].widget.can_add_related = False
        form.base_fields["part"].widget.can_view_related = False
        return form

    class Media:
        css = {
            "all": ("admin/css/ckeditor_modification.css",)
        }
        js = ("admin/js/ckeditor_modification.js",)


# DOCS INFO ---------------------------------------------------------------------------------------------------------- #
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
            qs_remaining = DocHeader.objects.order_by("-updated").exclude(pk__in=qs.values("pk"))
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

# MODERATION --------------------------------------------------------------------------------------------------------- #
# ...
