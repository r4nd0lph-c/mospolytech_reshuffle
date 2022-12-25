from django.db import models

from ckeditor.fields import RichTextField


class SingleActiveAbstract(models.Model):
    active = models.BooleanField(default=True, verbose_name="Актуальный")

    def save(self, *args, **kwargs):
        if self.active:
            type(self).objects.all().update(active=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = type(self).objects.order_by("-updated")
        qs = qs.exclude(pk=self.pk)
        if qs:
            qs.filter(pk=qs[0].pk).update(active=True)
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class DocsHeader(SingleActiveAbstract):
    content = RichTextField(config_name="Config_DocsHeader", verbose_name="Содержание")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    def __str__(self):
        state = "Актуальный" if self.active else "Неактуальный"
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = "Заголовок документа"
        verbose_name_plural = "Заголовки документа"

#
# class Subject(models.Model):
#     title = models.CharField(max_length=128, verbose_name="Название")
#     instr_title = models.CharField(max_length=128, default="Инструкция по выполнению работы",
#                                    verbose_name="Название инструкции")
#     instr_content = models.TextField(verbose_name="Содержимое инструкции")
#
#     def __str__(self):
#         return f"{self.title}"
#
#     class Meta:
#         verbose_name = "Предмет"
#         verbose_name_plural = "Предметы"
