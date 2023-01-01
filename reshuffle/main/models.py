from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import Group

from ckeditor.fields import RichTextField


class AbstractDatestamp(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("Date created"))
    date_updated = models.DateTimeField(auto_now=True, verbose_name=_("Date updated"))

    class Meta:
        abstract = True


class Difficulty(AbstractDatestamp):
    MIN_LVL = 1
    MAX_LVL = 32

    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_LVL), MaxValueValidator(MAX_LVL)],
        unique=True,
        db_index=True,
        default=1,
        help_text=_("Available range") + f": {MIN_LVL}…{MAX_LVL}.",
        verbose_name=_("Level")
    )
    description = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("A brief description of the difficulty level for colleagues to understand."),
        verbose_name=_("Description")
    )

    def __str__(self):
        desc = self.description if self.description else _("No description")
        return f"{self.level} ({desc})"

    class Meta:
        verbose_name = _("Difficulty")
        verbose_name_plural = _("Difficulties")


class Subject(AbstractDatestamp):
    pass


class Task(AbstractDatestamp):
    pass


class Option(AbstractDatestamp):
    pass


class DocHeader(AbstractDatestamp):
    content = RichTextField(
        config_name="Config_DocHeader",
        help_text=_("Information about the institution organizing the testing."),
        verbose_name=_("Content"))
    is_relevant = models.BooleanField(
        default=True,
        help_text=_("Only one relevant Document header can exist at a time."),
        verbose_name=_("Relevant")
    )

    def save(self, *args, **kwargs):
        if self.is_relevant:
            type(self).objects.all().update(is_relevant=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = type(self).objects.order_by("-date_updated")
        qs = qs.exclude(pk=self.pk)
        if qs:
            qs.filter(pk=qs[0].pk).update(is_relevant=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        state = _("Relevant") if self.is_relevant else _("Irrelevant")
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = _("Document header")
        verbose_name_plural = _("Document headers")


class Instruction(AbstractDatestamp):
    pass


class PartTitle(AbstractDatestamp):
    pass


class Part(AbstractDatestamp):
    pass


class AccessRight(AbstractDatestamp):
    pass


class HistoryLog(AbstractDatestamp):
    pass
