from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import Group

from ckeditor.fields import RichTextField


class AbstractDatestamp(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("Date created"))
    date_updated = models.DateTimeField(auto_now=True, verbose_name=_("Date updated"))

    class Meta:
        abstract = True


class Subject(AbstractDatestamp):
    pass


class Difficulty(AbstractDatestamp):
    pass


class Task(AbstractDatestamp):
    pass


class Option(AbstractDatestamp):
    pass


class DocHeader(AbstractDatestamp):
    content = RichTextField(config_name="Config_DocHeader", verbose_name=_("Content"))
    is_relevant = models.BooleanField(default=True, verbose_name=_("Relevant"))

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
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)


class PartTitle(AbstractDatestamp):
    pass


class Part(AbstractDatestamp):
    pass


class AccessRight(AbstractDatestamp):
    pass


class HistoryLog(AbstractDatestamp):
    pass
