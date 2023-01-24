from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter

from main.models import *


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ("id", "level", "description", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("level",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("case_nominative", "task_count", "total_difficulty")
        }),
        (_("Additional options"), {
            "classes": ("collapse",),
            "fields": ("case_genitive", "case_dative", "case_accusative", "case_instrumental", "case_prepositional")
        }),
    )
    list_display = ("id", "case_nominative", "task_count", "total_difficulty", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("-date_updated",)


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
    list_display = ("id", "subject", "title", "pretty_content", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("-date_updated",)
    list_filter = ("subject",)

    def pretty_content(self, obj):
        return mark_safe(f"<div style='border: 1px solid var(--hairline-color);'> {obj.content} </div>")

    pretty_content.short_description = Instruction._meta.get_field("content").verbose_name


@admin.register(PartTitle)
class PartTitleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("title",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    pass


@admin.register(AccessRight)
class AccessRightAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "subject", "date_created", "date_updated")
    list_display_links = ("id",)
    ordering = ("group", "subject")
    list_filter = ("group",)


@admin.register(HistoryLog)
class HistoryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "date_created")
    ordering = ("-date_created",)
    list_filter = ("user", ("date_created", DateFieldListFilter))

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = _("Administration")
