from django.utils.translation import gettext_lazy as _
from django.db import models
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

# UTILS -------------------------------------------------------------------------------------------------------------- #
DIFFICULTY_LVL = {
    0: _("Easy"),
    1: _("Medium"),
    2: _("Hard"),
}

PART_TITLES = {
    0: _("A"),
    1: _("B"),
    2: _("C"),
    3: _("D"),
}

PART_TYPES = {
    0: _("Tasks with answer choice"),
    1: _("Tasks with short answer writing"),
}

PART_NUMS = [15, 10]


def help_f(text: str) -> str:
    """ returns a formatted string for the help text field """

    return _("Tip") + ": " + text


class AbstractDatestamp(models.Model):
    """ adds additional date fields for child model classes """

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Date created"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Date updated"))

    class Meta:
        abstract = True


# TESTING MATERIALS -------------------------------------------------------------------------------------------------- #
class Subject(AbstractDatestamp):
    STR_LENGTH = 64

    sbj_title = models.CharField(
        max_length=STR_LENGTH,
        unique=True,
        db_index=True,
        help_text=help_f(_("Title of the subject (nominative case)")),
        verbose_name=_("Title")
    )
    case_genitive = models.CharField(max_length=STR_LENGTH, blank=True, verbose_name=_("Genitive case"))
    case_dative = models.CharField(max_length=STR_LENGTH, blank=True, verbose_name=_("Dative case"))
    case_accusative = models.CharField(max_length=STR_LENGTH, blank=True, verbose_name=_("Accusative case"))
    case_instrumental = models.CharField(max_length=STR_LENGTH, blank=True, verbose_name=_("Instrumental case"))
    case_prepositional = models.CharField(max_length=STR_LENGTH, blank=True, verbose_name=_("Prepositional case"))
    inst_title = models.CharField(
        max_length=STR_LENGTH,
        default=_("Instruction for work performance"),
        help_text=help_f(_("Title of the instruction")),
        verbose_name=_("Title")
    )
    inst_content = RichTextField(
        blank=True,
        config_name="config_1",
        help_text=help_f(_("List of general rules for work performance (without specific parts)")),
        verbose_name=_("Content")
    )
    is_active = models.BooleanField(
        default=False,
        help_text=help_f(_("Determines if this subject is available in the test generation list")),
        verbose_name=_("Activity")
    )

    def __str__(self):
        return self.sbj_title

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")


class Part(AbstractDatestamp):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text=help_f(_("Subject to which the part belongs")),
        verbose_name=_("Subject")
    )
    title = models.PositiveSmallIntegerField(
        choices=PART_TITLES,
        help_text=help_f(_("Select a subject to enable this field")),
        verbose_name=_("Title")
    )
    answer_type = models.PositiveSmallIntegerField(
        choices=PART_TYPES,
        help_text=help_f(_("Select a subject to enable this field")),
        verbose_name=_("Type of tasks")
    )
    task_count = models.PositiveSmallIntegerField(
        help_text=help_f(_("Select a type of tasks to enable this field")),
        verbose_name=_("Number of tasks")
    )
    total_difficulty = models.PositiveSmallIntegerField(
        help_text=help_f(_("Select a number of tasks to enable this field")),
        verbose_name=_("Total difficulty")
    )
    inst_content = RichTextField(
        blank=True,
        config_name="config_1",
        help_text=help_f(_("List of rules for performing the tasks of this part")),
        verbose_name=_("Content")
    )

    def __str__(self):
        return f"{self.subject}, " + _("Part") + f" {PART_TITLES[self.title]}"

    class Meta:
        verbose_name = _("Part")
        verbose_name_plural = _("Parts")


# DOCS INFO ---------------------------------------------------------------------------------------------------------- #
class DocHeader(AbstractDatestamp):
    content = RichTextField(
        config_name="config_1",
        help_text=help_f(_("Information about the institution organizing the testing")),
        verbose_name=_("Content")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=help_f(_("Only one active document header can exist at a time")),
        verbose_name=_("Activity")
    )

    def save(self, *args, **kwargs):
        if self.is_active:
            type(self).objects.all().update(is_active=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = type(self).objects.order_by("-updated")
        qs = qs.exclude(pk=self.pk)
        if qs:
            qs.filter(pk=qs[0].pk).update(is_active=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        state = _("Active") if self.is_active else _("Inactive")
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = _("Document header")
        verbose_name_plural = _("Document headers")

# MODERATION --------------------------------------------------------------------------------------------------------- #
# ...
