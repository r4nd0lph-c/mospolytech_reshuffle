from django.contrib.auth.models import Group
from django.db import models

from ckeditor.fields import RichTextField


class AbstractDatestamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractSingleFlag(AbstractDatestamp):
    flag = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.flag:
            type(self).objects.all().update(flag=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = type(self).objects.order_by("-updated")
        qs = qs.exclude(pk=self.pk)
        if qs:
            qs.filter(pk=qs[0].pk).update(flag=True)
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class DocHeader(AbstractSingleFlag):
    content = RichTextField(config_name="Config_DocHeader", verbose_name="Содержание")

    def __str__(self):
        state = "Актуальный" if self.flag else "Неактуальный"
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = "Заголовок документа"
        verbose_name_plural = "Заголовки документа"


DocHeader._meta.get_field("created").verbose_name = "Создан"
DocHeader._meta.get_field("updated").verbose_name = "Обновлён"
DocHeader._meta.get_field("flag").verbose_name = "Актуальный"


class Subject(AbstractDatestamp):
    title = models.CharField(max_length=128, verbose_name="Название")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"


Subject._meta.get_field("created").verbose_name = "Создан"
Subject._meta.get_field("updated").verbose_name = "Обновлён"


class AccessRight(AbstractDatestamp):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name="Доступные предметы")

    class Meta:
        verbose_name = "Право доступа"
        verbose_name_plural = "Права доступа"


AccessRight._meta.get_field("created").verbose_name = "Создано"
AccessRight._meta.get_field("updated").verbose_name = "Обновлено"
