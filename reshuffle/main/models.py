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
    content = RichTextField(config_name="Config_DocsHeader", verbose_name="Содержание")

    def __str__(self):
        state = "Актуальный" if self.flag else "Неактуальный"
        return f"ID: {self.id} ({state})"

    class Meta:
        verbose_name = "Заголовок документа"
        verbose_name_plural = "Заголовки документа"


DocHeader._meta.get_field("created").verbose_name = "Создан"
DocHeader._meta.get_field("updated").verbose_name = "Обновлён"
DocHeader._meta.get_field("flag").verbose_name = "Актуальный"

# class Subject(models.Model):
#     title = models.CharField(max_length=128, verbose_name="Название")
#     instr_title = models.CharField(max_length=128, default="Инструкция по выполнению работы",
#                                    verbose_name="Название инструкции")
#     instr_content = models.TextField(verbose_name="Содержимое инструкции")
#
#     def clean(self):
#         print("cleaned!")
#         cleaned_data = super().clean()
#
#     def __str__(self):
#         return f"{self.title}"
#
#     class Meta:
#         verbose_name = "Предмет"
#         verbose_name_plural = "Предметы"
