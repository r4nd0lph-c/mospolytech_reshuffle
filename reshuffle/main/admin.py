from django.utils.translation import gettext_lazy as _
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

# DOCS INFO ---------------------------------------------------------------------------------------------------------- #
# ...


# MODERATION --------------------------------------------------------------------------------------------------------- #
# ...
