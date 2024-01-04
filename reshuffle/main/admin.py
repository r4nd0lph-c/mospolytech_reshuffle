from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import admin
from reshuffle.settings import PROJECT_NAME
from main.models import *

# UTILS -------------------------------------------------------------------------------------------------------------- #
admin.site.site_title = PROJECT_NAME
admin.site.site_header = PROJECT_NAME
admin.site.index_title = _("Administration")


# TESTING MATERIALS -------------------------------------------------------------------------------------------------- #
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("case_nominative", "is_active",)
        }),
        (_("Additional options"), {
            "classes": ("collapse",),
            "fields": ("case_genitive", "case_dative", "case_accusative", "case_instrumental", "case_prepositional",)
        }),
    )
    list_display = ("id", "case_nominative", "is_active", "created", "updated",)
    list_display_links = ("id",)
    ordering = ("-updated",)
    list_filter = ("is_active",)


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
