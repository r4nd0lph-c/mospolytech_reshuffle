import json
import cv2
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
from main.services.docs.factory import DocumentPackager, GeneratorJSON
from main.services.ocr.analyzer import Analyzer

# UTILS -------------------------------------------------------------------------------------------------------------- #
PAGINATION_N = 10

minio_client = MinioClient()
analyzer = Analyzer()


class ObjectStorageListView(LoginRequiredMixin, ListView):
    """ Parent for Creation CBV & Download CBV """

    login_url = reverse_lazy("auth")
    paginate_by = PAGINATION_N

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["table_head"] = [
            ObjectStorageEntry._meta.get_field("subject").verbose_name,
            ObjectStorageEntry._meta.get_field("date").verbose_name,
            ObjectStorageEntry._meta.get_field("amount").verbose_name,
            ObjectStorageEntry._meta.get_field("user").verbose_name,
            ObjectStorageEntry._meta.get_field("created").verbose_name,
            _("Download")
        ]
        return context

    def get_queryset(self):
        qs = ObjectStorageEntry.objects.all().order_by("-created")
        groups = self.request.user.groups.all()
        if self.request.user.is_superuser or not groups.exists():
            return qs
        accesses = []
        for g in groups:
            accesses += [a.subject.id for a in Access.objects.filter(group=g)]
        return qs.filter(subject__id__in=accesses)


class VerificationChildTemplateView(LoginRequiredMixin, TemplateView):
    """ Parent for Capture CBV & Score CBV """

    login_url = reverse_lazy("auth")

    def get(self, request, *args, **kwargs):
        qs = ObjectStorageEntry.objects.filter(prefix=kwargs["prefix"])
        groups = self.request.user.groups.all()
        if not self.request.user.is_superuser and groups.exists():
            accesses = []
            for g in groups:
                accesses += [a.subject.id for a in Access.objects.filter(group=g)]
                qs = qs.filter(subject__id__in=accesses)
        if qs.first():
            return super().get(request, *args, **kwargs)
        return redirect(reverse_lazy("verification"))

    def get_context_data(self, **kwargs):
        archive = ObjectStorageEntry.objects.get(prefix=kwargs["prefix"])
        data = json.loads(minio_client.get_object_content(f"{kwargs['prefix']}/{GeneratorJSON.OUTPUT_JSON}"))
        qs_verified = VerifiedWorkEntry.objects.filter(archive=archive)
        uk_verified = qs_verified.values_list("unique_key", flat=True)
        uk_unverified = [v["unique_key"] for v in data["variants"] if v["unique_key"] not in uk_verified]
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["table_head"] = [
            VerifiedWorkEntry._meta.get_field("unique_key").verbose_name,
            VerifiedWorkEntry._meta.get_field("score").verbose_name,
            VerifiedWorkEntry._meta.get_field("user").verbose_name,
            _("Date verified")
        ]
        context["verified_table_body"] = qs_verified
        context["unverified_table_body"] = uk_unverified
        context["verified_count"] = qs_verified.count()
        context["unverified_count"] = archive.amount - context["verified_count"]
        context["amount"] = archive.amount
        context["percentage"] = round(context["verified_count"] / archive.amount * 100)
        return context


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


class Creation(ObjectStorageListView, FormView):
    template_name = "main/creation.html"
    form_class = CreationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Creation") + " | " + PROJECT_NAME
        context["subtitle"] = _("Create a set of entrance exams")
        context["datepicker_language"] = LANGUAGE_CODE
        context["avg_generate_time"] = config("AVG_GENERATE_TIME")
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
        dp.pack(
            user_id=self.request.user.id,
            sbj_id=form.cleaned_data["subject"].id,
            count=form.cleaned_data["amount"],
            date=form.cleaned_data["date"].strftime("%d.%m.%Y")
        )
        return redirect(reverse_lazy("download"))


class Download(ObjectStorageListView):
    template_name = "main/download.html"

    def get_context_data(self, **kwargs):
        qs = ObjectStorageEntry.objects.filter(user=self.request.user).order_by("-created")
        context = super().get_context_data(**kwargs)
        context["title"] = _("Download") + " | " + PROJECT_NAME
        context["subtitle"] = _("Download a set of entrance exams")
        context["prefix_created"] = qs[0].prefix if qs else None
        return context


class Verification(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("auth")
    paginate_by = PAGINATION_N
    template_name = "main/verification.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Verification") + " | " + PROJECT_NAME
        context["subtitle"] = _("Verify works of applicants")
        context["table_head"] = [
            ObjectStorageEntry._meta.get_field("subject").verbose_name,
            ObjectStorageEntry._meta.get_field("date").verbose_name,
            _("Verified") + f" ({ObjectStorageEntry._meta.get_field("amount").verbose_name})",
            ObjectStorageEntry._meta.get_field("user").verbose_name,
            ObjectStorageEntry._meta.get_field("created").verbose_name,
            _("Download")
        ]
        return context

    def get_queryset(self):
        qs = ObjectStorageEntry.objects.all().order_by("-created")
        for obj in qs:
            obj.verified_count = VerifiedWorkEntry.objects.filter(archive=obj).count()
        groups = self.request.user.groups.all()
        if self.request.user.is_superuser or not groups.exists():
            return qs
        accesses = []
        for g in groups:
            accesses += [a.subject.id for a in Access.objects.filter(group=g)]
        return qs.filter(subject__id__in=accesses)


class Capture(VerificationChildTemplateView):
    template_name = "main/capture.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Capture") + " | " + PROJECT_NAME
        context["subtitle"] = _("Select the work to be verified")
        return context


class Score(VerificationChildTemplateView):
    template_name = "main/score.html"

    def get(self, request, *args, **kwargs):
        data = json.loads(minio_client.get_object_content(f"{kwargs['prefix']}/{GeneratorJSON.OUTPUT_JSON}"))
        for v in data["variants"]:
            if kwargs["unique_key"] == v["unique_key"]:
                return super().get(request, *args, **kwargs)
        return redirect(reverse_lazy("verification"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Score") + " | " + PROJECT_NAME
        context["subtitle"] = _("Score the work of applicant")
        return context


def download_archive(request, prefix: str = None):
    if request.method == "GET":
        if request.user.is_authenticated:
            if prefix:
                # redirect to generated tmp link
                return redirect(minio_client.get_object_url(f"{prefix}.{DocumentPackager.ARCHIVE_FORMAT}"))
    # generate JSON response (error)
    return JsonResponse({"error": "you don't have enough permissions"})


def recognize(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            # get data from request
            prefix = request.POST.get("prefix")
            img_path = request.FILES.get("image").temporary_file_path()
            # recognize the unique key of the uploaded work
            try:
                img_base = cv2.imread(img_path)
                img_grayscale = analyzer.grayscale(img_base)
                img_restore_perspective = analyzer.restore_perspective(img_grayscale)
                img_threshold = analyzer.threshold(img_restore_perspective)
                stats = analyzer.calc_stats(img_threshold)
                data = json.loads(minio_client.get_object_content(f"{prefix}/{GeneratorJSON.OUTPUT_JSON}"))
                uk = analyzer.get_unique_key(img_threshold, stats, data)
                # generate JSON response (recognized)
                return JsonResponse({
                    "recognized": True,
                    "unique_key": uk
                })
            except Exception:
                # generate JSON response (unrecognized)
                return JsonResponse({
                    "recognized": False,
                    "unique_key": None
                })
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
