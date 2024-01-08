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
            id_title = request.GET.get("id_title", "None")
            id_title = int(id_title) if id_title else None

            # generates available & reserved part_titles dicts + nums_reserved list
            part_titles_available = Part.TITLES.copy()
            part_titles_reserved = {}
            nums_reserved = []
            if id_sbj:
                for part in Part.objects.filter(subject__pk=id_sbj):
                    if part.title != id_title:
                        del part_titles_available[part.title]
                        part_titles_reserved[part.title] = Part.TITLES[part.title]
                        nums_reserved.append([part.answer_type, part.task_count])

            # generates JSON correct response
            return JsonResponse({
                "subject": (id_sbj, Subject.objects.get(pk=id_sbj).sbj_title) if id_sbj else (None, None),
                "difficulties": DIFFICULTIES,
                "remained_amount": Part.AMOUNT - sum([ceil(n[1] / Part.CAPACITIES[n[0]]) for n in nums_reserved]),
                "titles": {
                    "available": part_titles_available,
                    "reserved": part_titles_reserved,
                },
                "labels": Part.LABELS,
            })

        # generates JSON error response
        return JsonResponse({"error": "you don't have enough permissions"})


# ERRORS ------------------------------------------------------------------------------------------------------------- #
def page_not_found(request, exception):
    return HttpResponseNotFound("Error 404")
