# TODO: add max_length for DocHeader.content (RichTextField)
# TODO: add max_length for Option.content (RichTextField) (if Part.answer_type == 1)

from math import ceil
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import Group
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

# UTILS -------------------------------------------------------------------------------------------------------------- #
DIFFICULTIES = {
    0: _("Easy"),
    1: _("Medium"),
    2: _("Hard"),
}


class AbstractDatestamp(models.Model):
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
        help_text=_("Title of the subject (nominative case)"),
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
        help_text=_("Title of the instruction"),
        verbose_name=_("Title")
    )
    inst_content = RichTextField(
        blank=True,
        config_name="config_1",
        help_text=_("List of general rules for work performance (without specific parts)"),
        verbose_name=_("Content")
    )
    is_active = models.BooleanField(
        default=False,
        help_text=_("Determines if this subject is available in the test generation list"),
        verbose_name=_("Activity")
    )

    def __str__(self):
        return self.sbj_title

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = " " * 4 + _("Subjects")


class Part(AbstractDatestamp):
    AMOUNT = 4
    TITLES = {
        0: _("A"),
        1: _("B"),
        2: _("C"),
        3: _("D"),
    }
    TYPES = {
        0: _("Tasks with answer choice"),
        1: _("Tasks with short answer writing"),
    }
    CAPACITIES = [15, 10]
    LABELS = [
        [
            _("Select a subject to enable this field"),
            _("Select a subject to enable this field"),
            _("Select a type of tasks to enable this field"),
            _("Select a count of tasks to enable this field"),
        ],
        [
            _("Reserved title(s)"),
            _("Select a type of tasks in the part"),
            _("Available count of tasks taking into account the previous parts and the selected task type"),
            _("The recommended difficulty is set, difficulty range"),
        ],
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text=_("Subject to which the part belongs"),
        verbose_name=_("Subject")
    )
    title = models.PositiveSmallIntegerField(
        choices=TITLES,
        help_text=LABELS[0][0],
        verbose_name=_("Title")
    )
    answer_type = models.PositiveSmallIntegerField(
        choices=TYPES,
        help_text=LABELS[0][1],
        verbose_name=_("Type of tasks")
    )
    task_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text=LABELS[0][2],
        verbose_name=_("Tasks")
    )
    total_difficulty = models.PositiveSmallIntegerField(
        help_text=LABELS[0][3],
        verbose_name=_("Difficulty")
    )
    inst_content = RichTextField(
        blank=True,
        config_name="config_1",
        help_text=_("List of rules for performing the tasks of this part"),
        verbose_name=_("Content")
    )

    def clean(self, *args, **kwargs):
        # title
        amount = Part.AMOUNT
        titles_available = Part.TITLES.copy()
        exception = Part.objects.get(id=self.id).title if self.id else -1
        for part in Part.objects.filter(subject__id=self.subject_id):
            if part.title != exception:
                del titles_available[part.title]
                amount -= ceil(part.task_count / Part.CAPACITIES[part.answer_type])
        if self.title not in titles_available.keys():
            raise ValidationError({
                "title": _("Available title(s)") + f": [{', '.join([str(t) for t in titles_available.values()])}]."
            })
        # answer_type
        if self.answer_type is None:
            raise ValidationError({})
        # task_count
        if self.task_count is None:
            raise ValidationError({})
        count_max = amount * Part.CAPACITIES[self.answer_type]
        count_min = 0 if 1 > count_max else 1
        if not (count_min <= self.task_count <= count_max):
            raise ValidationError({
                "task_count": _("Invalid value") + "."
            })
        # total_difficulty
        if self.total_difficulty is None:
            raise ValidationError({})
        difficulty_max = self.task_count * list(DIFFICULTIES.keys())[-1]
        difficulty_min = 0 if 1 > difficulty_max else list(DIFFICULTIES.keys())[0]
        if self.total_difficulty:
            if not (difficulty_min <= self.total_difficulty <= difficulty_max):
                raise ValidationError({
                    "total_difficulty": _("Invalid value") + "."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject}, " + _("Part") + f" {Part.TITLES[self.title]}"

    class Meta:
        verbose_name = _("Part")
        verbose_name_plural = " " * 3 + _("Parts")


class Task(AbstractDatestamp):
    LABELS = [
        _("Select a part to enable this field"),
        _("Order number of the task in the part, range of valid positions"),
    ]

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        help_text=_("Subject and part to which the task relates"),
        verbose_name=_("Part")
    )
    position = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text=LABELS[0],
        verbose_name=_("Position")
    )
    content = RichTextUploadingField(
        config_name="config_2",
        help_text=_("The essence of the task"),
        verbose_name=_("Content")
    )
    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTIES,
        help_text=_("Difficulty of the task relative to other tasks of the same order number"),
        verbose_name=_("Difficulty")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Determines if this task is included in document generation"),
        verbose_name=_("Activity")
    )

    def clean(self, *args, **kwargs):
        # position
        if not self.position:
            raise ValidationError({})
        if not (1 <= self.position <= Part.objects.get(id=self.part.id).task_count):
            raise ValidationError({
                "position": _("Invalid value") + "."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ID: {self.id} ({self.part}, {Part.TYPES[self.part.answer_type]}, {self.position})"

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = " " * 2 + _("Tasks")


class Option(AbstractDatestamp):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        help_text=_("Task to which the option relates"),
        verbose_name=_("Task")
    )
    content = RichTextUploadingField(
        config_name="config_2",
        help_text=_("The essence of the option"),
        verbose_name=_("Content")
    )
    is_answer = models.BooleanField(
        default=False,
        help_text=_("Determines if this option is the correct answer"),
        verbose_name=_("Correct answer")
    )

    def __str__(self):
        return f"{self.task}, {self.is_answer}"

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = " " * 1 + _("Options")


# DOCS INFO ---------------------------------------------------------------------------------------------------------- #
class DocHeader(AbstractDatestamp):
    content = RichTextField(
        config_name="config_1",
        help_text=_("Information about the institution organizing the testing"),
        verbose_name=_("Content")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Only one active document header can exist at a time"),
        verbose_name=_("Activity")
    )

    def save(self, *args, **kwargs):
        if self.is_active:
            type(self).objects.all().update(is_active=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = type(self).objects.order_by("-updated")
        qs = qs.exclude(id=self.id)
        if qs:
            qs.filter(id=qs[0].id).update(is_active=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        state = _("Active") if self.is_active else _("Inactive")
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = _("Document header")
        verbose_name_plural = " " * 5 + _("Document headers")


# MODERATION --------------------------------------------------------------------------------------------------------- #
class Access(AbstractDatestamp):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text=_("Group for which access to subjects is granted"),
        verbose_name=_("Group")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text=_("One of the subjects that will be available for interaction by the selected group"),
        verbose_name=_("Subject")
    )

    def __str__(self):
        return f"ID: {self.id} ({self.group})"

    class Meta:
        app_label = "auth"
        verbose_name = _("Access")
        verbose_name_plural = _("Accesses")
