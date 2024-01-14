from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseNotFound, JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from reshuffle.settings import PROJECT_NAME
from main.forms import *
from main.models import *


# MAIN VIEWS --------------------------------------------------------------------------------------------------------- #
class Index(LoginRequiredMixin, TemplateView):
    template_name = "main/index.html"
    login_url = reverse_lazy("auth")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Main") + " | " + PROJECT_NAME
        return context


class Auth(LoginView):
    form_class = AuthForm
    template_name = "main/auth.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Auth") + " | " + PROJECT_NAME
        return context

    def form_valid(self, form):
        remember_me = form.cleaned_data["remember_me"]
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super(Auth, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("index")


def logout_user(request):
    logout(request)
    return redirect("auth")


# VALIDATORS --------------------------------------------------------------------------------------------------------- #
def validation_part(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            # get data from request
            id_sbj = int(request.GET.get("id_sbj")) if request.GET.get("id_sbj") else None
            id_prt = int(request.GET.get("id_prt")) if request.GET.get("id_prt") else None
            # generate titles & capacities
            titles_available = Part.TITLES.copy()
            titles_reserved = {}
            capacities = []
            exception = Part.objects.get(pk=id_prt).title if id_prt else -1
            if id_sbj:
                for part in Part.objects.filter(subject__pk=id_sbj):
                    if part.title != exception:
                        titles_reserved[part.title] = titles_available.pop(part.title)
                        capacities.append([part.task_count, part.answer_type])
            # generate JSON response (correct)
            return JsonResponse({
                "difficulties": DIFFICULTIES,
                "amount": max(0, Part.AMOUNT - sum([ceil(i[0] / Part.CAPACITIES[i[1]]) for i in capacities])),
                "capacities": Part.CAPACITIES,
                "titles": {
                    "available": titles_available,
                    "reserved": titles_reserved,
                },
                "labels": Part.LABELS
            })
        # generate JSON response (error)
        return JsonResponse({"error": "you don't have enough permissions"})


def validation_task(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            # get data from request
            id_prt = int(request.GET.get("id_prt")) if request.GET.get("id_prt") else None
            # generate JSON response (correct)
            return JsonResponse({
                "amount_min": 1 if id_prt else 0,
                "amount_max": Part.objects.get(pk=id_prt).task_count if id_prt else 0,
                "labels": Task.LABELS,
            })
        # generate JSON response (error)
        return JsonResponse({"error": "you don't have enough permissions"})


# ERRORS ------------------------------------------------------------------------------------------------------------- #
def page_not_found(request, exception):
    return HttpResponseNotFound("Error 404")
