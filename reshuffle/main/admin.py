from django.contrib import admin
from django.utils.safestring import mark_safe

from main.models import *


@admin.register(DocHeader)
class DocHeaderAdmin(admin.ModelAdmin):
    fields = ("content", "is_active")
    list_display = ("id", "pretty_content", "created", "updated", "is_active")
    list_display_links = ("id",)
    ordering = ("-updated",)
    list_filter = ("is_active",)

    def pretty_content(self, obj):
        return mark_safe(f"<div style='border: 1px solid var(--hairline-color);'> {obj.content} </div>")

    pretty_content.short_description = DocHeader._meta.get_field("content").verbose_name

    def delete_queryset(self, request, qs):
        if qs.filter(is_active=True):
            qs_remaining = DocHeader.objects.order_by("-updated").exclude(pk__in=qs.values("pk"))
            if qs_remaining:
                is_active_new = qs_remaining[0]
                is_active_new.is_active = True
                is_active_new.save()
        qs.delete()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    list_display_links = ("id",)


@admin.register(PartTitle)
class PartTitleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_global")
    list_display_links = ("id",)
    # ordering = ("-created",)


@admin.register(AccessRight)
class AccessRightAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "pretty_subjects")
    list_display_links = ("id",)
    filter_horizontal = ("subjects",)

    def pretty_subjects(self, obj):
        return ", ".join(sbj.title for sbj in obj.subjects.all())

    pretty_subjects.short_description = AccessRight._meta.get_field("subjects").verbose_name


admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = "Администрирование"
