from decouple import config
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView, FormView, ListView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from reshuffle.settings import PROJECT_NAME, LANGUAGE_CODE
from main.forms import *
from main.models import *
from main.services.docs.minio_client import MinioClient
from main.services.docs.factory import DocumentPackager


# MAIN VIEWS --------------------------------------------------------------------------------------------------------- #
class Auth(LoginView):
    template_name = "main/auth.html"
    form_class = AuthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Auth") + " | " + PROJECT_NAME
        context["subtitle"] = _("Entrance exam processing system")
        return context

    def form_valid(self, form):
        remember_me = form.cleaned_data["remember_me"]
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super(Auth, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("index")


class Index(LoginRequiredMixin, TemplateView):
    template_name = "main/index.html"
    login_url = reverse_lazy("auth")

    def get_context_data(self, **kwargs):
        r = self.request
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Main") + " | " + PROJECT_NAME
        context["subtitle"] = _("Select an activity")
        context["user_full_name"] = r.user.get_full_name() if r.user.get_full_name() else r.user.username
        return context


class Creation(LoginRequiredMixin, FormView, ListView):
    template_name = "main/creation.html"
    login_url = reverse_lazy("auth")
    form_class = CreationForm
    paginate_by = 2
    model = ObjectStorageEntry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Creation") + " | " + PROJECT_NAME
        context["subtitle"] = _("Create a set of entrance exams")
        context["datepicker_language"] = LANGUAGE_CODE
        context["avg_generate_time"] = config("AVG_GENERATE_TIME")
        context["table_head"] = [
            ObjectStorageEntry._meta.get_field("subject").verbose_name,
            ObjectStorageEntry._meta.get_field("amount").verbose_name,
            ObjectStorageEntry._meta.get_field("date").verbose_name,
            ObjectStorageEntry._meta.get_field("user").verbose_name,
            ObjectStorageEntry._meta.get_field("created").verbose_name,
            _("Download")
        ]
        return context

    def get_form_kwargs(self):
        kwargs = super(Creation, self).get_form_kwargs()
        qs = Subject.objects.filter(is_active=True)
        groups = self.request.user.groups.all()
        if self.request.user.is_superuser or not groups.exists():
            kwargs["subject_choices"] = qs
        else:
            accesses = []
            for g in groups:
                accesses += [a.subject.id for a in Access.objects.filter(group=g)]
            kwargs["subject_choices"] = qs.filter(id__in=accesses)
        return kwargs

    def form_valid(self, form):
        dp = DocumentPackager()
        prefix = dp.pack(
            user_id=self.request.user.id,
            sbj_id=form.cleaned_data["subject"].id,
            count=form.cleaned_data["amount"],
            date=form.cleaned_data["date"].strftime("%d.%m.%Y")
        )
        return redirect(f"{reverse_lazy("download")}?prefix={prefix}")


def download(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            prefix = request.GET.get("prefix") if request.GET.get("prefix") else None
            if prefix:
                # redirect to generated tmp link
                mc = MinioClient()
                return redirect(mc.get_object_url(f"{prefix}.{DocumentPackager.ARCHIVE_FORMAT}"))
    # generate JSON response (error)
    return JsonResponse({"error": "you don't have enough permissions"})


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
    response = render(
        request,
        "main/404.html",
        {
            "project_name": PROJECT_NAME.upper(),
            "title": _("Page not Found") + " | " + PROJECT_NAME
        }
    )
    response.status_code = 404
    return response
