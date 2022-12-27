from django.contrib import admin
from django.utils.safestring import mark_safe

from main.models import *


@admin.register(DocHeader)
class DocHeaderAdmin(admin.ModelAdmin):
    fields = ("content", "flag")
    list_display = ("id", "pretty_content", "created", "updated", "flag")
    list_display_links = ("id",)
    ordering = ("-updated",)
    list_filter = ("flag",)

    def pretty_content(self, obj):
        return mark_safe(f"<div style='border: 1px solid var(--hairline-color);'> {obj.content} </div>")

    pretty_content.short_description = DocHeader._meta.get_field("content").verbose_name

    def delete_queryset(self, request, qs):
        if qs.filter(flag=True):
            qs_remaining = DocHeader.objects.order_by("-updated").exclude(pk__in=qs.values("pk"))
            if qs_remaining:
                flag_new = qs_remaining[0]
                flag_new.flag = True
                flag_new.save()
        qs.delete()


# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ("id", "title", "created", "updated", "active")
#     list_display_links = ("id",)
#     ordering = ("-updated",)
#     list_filter = ("active",)

# TODO: abstract class for created updated fix qs = type(self).objects.order_by("-updated") (models.py [15])

admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = "Администрирование"
