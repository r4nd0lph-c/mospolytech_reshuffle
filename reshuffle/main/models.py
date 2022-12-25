from ckeditor.fields import RichTextField
from django.db import models


class SingleActiveAbstract(models.Model):
    active = models.BooleanField(default=True, editable=False, verbose_name="Актуальный")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.active:
            qs = type(self).objects.filter(active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(active=False)
        super(SingleActiveAbstract, self).save(*args, **kwargs)


class DocsHeader(SingleActiveAbstract):
    content = RichTextField(config_name="Config_DocsHeader", verbose_name="Содержание")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = "Заголовок документа"
        verbose_name_plural = "Заголовки документа"
