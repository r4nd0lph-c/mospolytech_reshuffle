from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseNotFound
from django.views.generic import TemplateView
from reshuffle.settings import PROJECT_NAME


class Index(TemplateView):
    template_name = "main/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Main") + " | " + PROJECT_NAME
        return context


def page_not_found(request, exception):
    return HttpResponseNotFound("Error 404")
