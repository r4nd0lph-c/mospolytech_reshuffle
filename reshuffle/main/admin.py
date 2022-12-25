from django.contrib import admin
from django.utils.safestring import mark_safe

from main.models import *


@admin.register(DocsHeader)
class DocsHeaderAdmin(admin.ModelAdmin):
    fields = ("content", "active")
    list_display = ("id", "pretty_content", "created", "updated", "active")
    list_display_links = ("id",)
    ordering = ("-updated",)
    list_filter = ("active",)

    def pretty_content(self, obj):
        return mark_safe(f"<div style='border: 1px solid var(--hairline-color);'> {obj.content} </div>")

    pretty_content.short_description = DocsHeader._meta.get_field("content").verbose_name

    def delete_queryset(self, request, qs):
        if qs.filter(active=True):
            qs_remaining = DocsHeader.objects.order_by("-updated").exclude(pk__in=qs.values("pk"))
            if qs_remaining:
                active_new = qs_remaining[0]
                active_new.active = True
                active_new.save()
        qs.delete()


admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = "Администрирование"
