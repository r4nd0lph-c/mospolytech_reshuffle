from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import admin

from main.models import *


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ("id", "level", "description", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("level",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    pass


@admin.register(DocHeader)
class DocHeaderAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "date_created", "date_updated", "is_relevant")
    list_display_links = ("id",)
    ordering = ("-date_updated",)
    list_filter = ("is_relevant",)

    def pretty_content(self, obj):
        return mark_safe(f"<div style='border: 1px solid var(--hairline-color);'> {obj.content} </div>")

    pretty_content.short_description = DocHeader._meta.get_field("content").verbose_name

    def delete_queryset(self, request, qs):
        if qs.filter(is_relevant=True):
            qs_remaining = DocHeader.objects.order_by("-date_updated").exclude(pk__in=qs.values("pk"))
            if qs_remaining:
                relevant = qs_remaining[0]
                relevant.is_relevant = True
                relevant.save()
        qs.delete()


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    pass


@admin.register(PartTitle)
class PartTitleAdmin(admin.ModelAdmin):
    pass


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    pass


@admin.register(AccessRight)
class AccessRightAdmin(admin.ModelAdmin):
    pass


@admin.register(HistoryLog)
class HistoryLogAdmin(admin.ModelAdmin):
    pass


admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = _("Administration")
