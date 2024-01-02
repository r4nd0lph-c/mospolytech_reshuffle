from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from reshuffle.settings import PROJECT_NAME

admin.site.site_title = PROJECT_NAME
admin.site.site_header = PROJECT_NAME
admin.site.index_title = _("Administration")
