from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
        return f"ID: {self.id} " + _("Level") + f": {self.level}"

    class Meta:
        verbose_name = _("Difficulty")
        verbose_name_plural = _("Difficulties")


class Subject(AbstractDatestamp):
    MIN_TC = 1
    MAX_TC = 999
    MIN_TD = Difficulty.MIN_LVL * MIN_TC
    MAX_TD = Difficulty.MAX_LVL * MAX_TC

    case_nominative = models.CharField(
        max_length=128,
        default="",
        help_text=_("Nominative case."),
        verbose_name=_("Title")
    )
    case_genitive = models.CharField(max_length=128, blank=True, verbose_name=_("Genitive case"))
    case_dative = models.CharField(max_length=128, blank=True, verbose_name=_("Dative case"))
    case_accusative = models.CharField(max_length=128, blank=True, verbose_name=_("Accusative case"))
    case_instrumental = models.CharField(max_length=128, blank=True, verbose_name=_("Instrumental case"))
    case_prepositional = models.CharField(max_length=128, blank=True, verbose_name=_("Prepositional case"))
    task_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_TC), MaxValueValidator(MAX_TC)],
        default=1,
        help_text=_("The total count of tasks in the test.") + " " + _("Available range") + f": {MIN_TC}…{MAX_TC}.",
        verbose_name=_("Task Count")
    )
    total_difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_TD), MaxValueValidator(MAX_TD)],
        default=1,
        help_text=_("Recommended overall test difficulty.") + " " + _("Available range") + f": {MIN_TD}…{MAX_TD}.",
        verbose_name=_("Total Difficulty")
    )

    def __str__(self):
        return f"ID: {self.id} ({self.case_nominative})"

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")


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
