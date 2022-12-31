from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from main.models import *

admin.site.site_title = "RESHUFFLE"
admin.site.site_header = "RESHUFFLE"
admin.site.index_title = _("Administration")
