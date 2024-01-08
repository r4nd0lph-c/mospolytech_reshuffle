from math import ceil
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseNotFound, JsonResponse
from django.views.generic import TemplateView
from reshuffle.settings import PROJECT_NAME
from main.models import *


# MAIN VIEWS --------------------------------------------------------------------------------------------------------- #
class Index(TemplateView):
    template_name = "main/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Main") + " | " + PROJECT_NAME
        return context


# VALIDATORS --------------------------------------------------------------------------------------------------------- #
def validation_part(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            # gets data from request
            id_sbj = request.GET.get("id_sbj", "None")
            id_sbj = int(id_sbj) if id_sbj else None

            # generates JSON correct response
            return JsonResponse({
                None: None
            })

        # generates JSON error response
        return JsonResponse({"error": "you don't have enough permissions"})


# ERRORS ------------------------------------------------------------------------------------------------------------- #
def page_not_found(request, exception):
    return HttpResponseNotFound("Error 404")
