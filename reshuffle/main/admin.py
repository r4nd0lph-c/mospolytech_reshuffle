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
    title = _("Instructions available")
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
    ordering = ("-updated",)
    list_filter = (InstAvailableFilter, "is_active",)

    def inst_available(self, obj: "Subject"):
        if obj.inst_content:
            return True
        return False

    inst_available.boolean = True
    inst_available.short_description = _("Instructions available")

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
