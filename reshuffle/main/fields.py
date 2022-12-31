from django.utils.translation import gettext_lazy as _
from django.db import models


class TotalDifficultyField(models.PositiveSmallIntegerField):
    description = _("TotalDifficulty input field")

    def db_type(self, connection):
        return "integer"
