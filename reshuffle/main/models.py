from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models

from ckeditor.fields import RichTextField


# -------------- ABSTRACT CLASSES -------------- #
class AbstractDatestamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------- #


# ---------------- MAIN CLASSES ---------------- #
class DocHeader(AbstractDatestamp):
    content = RichTextField(config_name="Config_DocHeader", verbose_name="Содержание")
    is_active = models.BooleanField(default=True, verbose_name="Актуальный")

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
        state = "Актуальный" if self.is_active else "Неактуальный"
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = "Заголовок документа"
        verbose_name_plural = "Заголовки документа"


DocHeader._meta.get_field("created").verbose_name = "Создан"
DocHeader._meta.get_field("updated").verbose_name = "Обновлён"


class Subject(AbstractDatestamp):
    title = models.CharField(max_length=128, verbose_name="Название")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"


Subject._meta.get_field("created").verbose_name = "Создан"
Subject._meta.get_field("updated").verbose_name = "Обновлён"


class PartTitle(models.Model):
    title = models.CharField(max_length=128, unique=True, db_index=True, verbose_name="Название")
    is_global = models.BooleanField(default=False)

    def clean(self):
        qs = PartTitle.objects.filter(is_global=True)
        if self.is_global and qs:
            msg = f"Глобальное {PartTitle._meta.verbose_name.lower()} уже существует. ID: {qs[0].pk} ({qs[0].title})."
            raise ValidationError({"is_global": msg})

    class Meta:
        verbose_name = "Название части"
        verbose_name_plural = "Названия частей"


# ---------------------------------------------- #


# ----------- ADMINISTRATION CLASSES ----------- #
class AccessRight(AbstractDatestamp):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name="Доступные предметы")

    class Meta:
        verbose_name = "Право доступа"
        verbose_name_plural = "Права доступа"


AccessRight._meta.get_field("created").verbose_name = "Создано"
AccessRight._meta.get_field("updated").verbose_name = "Обновлено"

# ---------------------------------------------- #
