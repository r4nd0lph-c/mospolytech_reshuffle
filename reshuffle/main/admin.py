from django.contrib import admin
from django.utils.safestring import mark_safe

from main.models import *


@admin.register(DocsHeader)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "pretty_content", "created", "updated", "active")
    list_display_links = ("id",)
    ordering = ("-created",)
    list_filter = ("active",)

    def pretty_content(self, obj):
        return mark_safe(obj.content)

    pretty_content.short_description = DocsHeader._meta.get_field("content").verbose_name


admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = "Администрирование"
