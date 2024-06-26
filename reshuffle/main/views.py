import json
import numpy as np
import cv2
from io import BytesIO
from uuid import uuid4
from decouple import config
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView, FormView, ListView
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from reshuffle.settings import PROJECT_NAME, LANGUAGE_CODE
from main.forms import *
from main.models import *
from minio.error import S3Error
from main.services.docs.minio_client import MinioClient
from main.services.docs.factory import DocumentPackager, GeneratorJSON
from main.services.ocr.analyzer import Analyzer

# UTILS -------------------------------------------------------------------------------------------------------------- #
PAGINATION_N = 10  # TODO: fix screen scroll for 1920x1080 size

IMAGE_FORMAT = "png"
FOLDER_CAPTURED = "captured"
FOLDER_SCORED = "scored"

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
        messages.error(request, _("The specified archive prefix is invalid"))
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
        fbi = FeedbackInfo.objects.filter(is_active=True).first()
        context = super().get_context_data(**kwargs)
        context["project_name"] = PROJECT_NAME.upper()
        context["title"] = _("Auth") + " | " + PROJECT_NAME
        context["subtitle"] = _("Entrance exam processing system")
        context["feedback_info"] = fbi.content if fbi else None
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
            _("Verification progress"),
            ObjectStorageEntry._meta.get_field("user").verbose_name,
            ObjectStorageEntry._meta.get_field("created").verbose_name,
            _("Download")
        ]
        return context

    def get_queryset(self):
        qs = ObjectStorageEntry.objects.all().order_by("-created")
        groups = self.request.user.groups.all()
        if not (self.request.user.is_superuser or not groups.exists()):
            accesses = []
            for g in groups:
                accesses += [a.subject.id for a in Access.objects.filter(group=g)]
            qs = qs.filter(subject__id__in=accesses)
        for obj in qs:
            obj.verified_count = VerifiedWorkEntry.objects.filter(archive=obj).count()
        return qs


class Capture(VerificationChildTemplateView):
    template_name = "main/capture.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Capture") + " | " + PROJECT_NAME
        context["subtitle"] = _("Select the work to be verified")
        return context


class Score(VerificationChildTemplateView, FormView):
    template_name = "main/score.html"
    form_class = ScoreForm

    def get(self, request, *args, **kwargs):
        try:
            data = json.loads(minio_client.get_object_content(f"{kwargs['prefix']}/{GeneratorJSON.OUTPUT_JSON}"))
            for v in data["variants"]:
                if kwargs["unique_key"] == v["unique_key"]:
                    try:
                        minio_client.get_object_stats(
                            alias=f"{kwargs['prefix']}/{FOLDER_CAPTURED}/{kwargs['unique_key']}.{IMAGE_FORMAT}"
                        )
                    except S3Error:
                        messages.error(request, _("The requested image was not found"))
                        return redirect(reverse_lazy("capture", kwargs={"prefix": kwargs["prefix"]}))
                    return super().get(request, *args, **kwargs)
            messages.error(
                request,
                _("The specified unique key is invalid") + f": <b class='uk'>{kwargs['unique_key']}</b>"
            )
            return redirect(reverse_lazy("capture", kwargs={"prefix": kwargs["prefix"]}))
        except S3Error:
            messages.error(request, _("The specified archive prefix is invalid"))
            return redirect(reverse_lazy("verification"))

    def get_context_data(self, **kwargs):
        alias = f"{kwargs['prefix']}/{FOLDER_CAPTURED}/{kwargs['unique_key']}.{IMAGE_FORMAT}"
        img_data = minio_client.get_object_content(alias=alias, decoded=False).data
        img_threshold = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_GRAYSCALE)
        variants = json.loads(
            minio_client.get_object_content(f"{kwargs['prefix']}/{GeneratorJSON.OUTPUT_JSON}")
        )["variants"]
        variant = list(filter(lambda v: v["unique_key"] == kwargs["unique_key"], variants))[0]
        try:
            stats = analyzer.calc_stats(img_threshold)
            f_answers, f_correction = analyzer.get_fields(img_threshold, stats, variant)
            score_result = analyzer.score(variant, f_answers, f_correction)
        except:
            variant["total_score"] = sum([p["info"]["task_count"] for p in variant["parts"]])
            variant["achieved_score"] = 0
            score_result = {"scored": False, "variant": variant}
        context = super().get_context_data(**kwargs)
        context["title"] = _("Score") + " | " + PROJECT_NAME
        context["subtitle"] = _("Score the work of applicant")
        context["img_threshold_url"] = minio_client.get_object_url(alias=alias)
        context["score_result"] = score_result
        return context

    def form_valid(self, form):
        prefix = form.cleaned_data["prefix"]
        unique_key = form.cleaned_data["unique_key"]
        score = form.cleaned_data["score"]
        try:
            entry = VerifiedWorkEntry.objects.get(
                archive=ObjectStorageEntry.objects.filter(prefix=prefix).first(),
                unique_key=unique_key
            )
            entry.delete()
        except ObjectDoesNotExist:
            pass
        finally:
            entry = VerifiedWorkEntry(
                user=self.request.user,
                archive=ObjectStorageEntry.objects.filter(prefix=prefix).first(),
                unique_key=unique_key,
                score=score,
                alias=f"{prefix}/{FOLDER_SCORED}/{unique_key}.{IMAGE_FORMAT}"
            )
            entry.save()
        minio_client.rename_object(
            alias_old=f"{prefix}/{FOLDER_CAPTURED}/{unique_key}.{IMAGE_FORMAT}",
            alias_new=f"{prefix}/{FOLDER_SCORED}/{unique_key}.{IMAGE_FORMAT}"
        )
        messages.success(
            self.request,
            _("The work is scored") + f": <b class='uk'>{unique_key}</b> <b>({score})</b>"
        )
        return redirect(reverse_lazy("capture", kwargs={"prefix": form.cleaned_data['prefix']}))


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
                # process image
                img_base = cv2.imread(img_path)
                img_grayscale = analyzer.grayscale(img_base)
                img_restore_perspective = analyzer.restore_perspective(img_grayscale)
                img_threshold = analyzer.threshold(img_restore_perspective)
                stats = analyzer.calc_stats(img_threshold)
                data = json.loads(minio_client.get_object_content(f"{prefix}/{GeneratorJSON.OUTPUT_JSON}"))
                uk = analyzer.get_unique_key(img_threshold, stats, data)
                # save processed image to storage
                _, buffer = cv2.imencode(f".{IMAGE_FORMAT}", img_threshold)
                obj = BytesIO(buffer.tobytes())
                name = uk if uk else str(uuid4())
                minio_client.upload_bytes(
                    obj=obj,
                    alias=f"{prefix}/{FOLDER_CAPTURED}/{name}.{IMAGE_FORMAT}",
                    length=obj.getbuffer().nbytes
                )
                # generate JSON response (recognized)
                return JsonResponse({"recognized": True, "unique_key": uk, "alias": name})
            except:
                # generate JSON response (unrecognized)
                return JsonResponse({"recognized": False, "unique_key": None, "alias": None})
    # generate JSON response (error)
    return JsonResponse({"error": "you don't have enough permissions"})


def rename_alias(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            # get data from request
            prefix = request.POST.get("prefix") if request.POST.get("prefix") else None
            alias_old = request.POST.get("alias_old") if request.POST.get("alias_old") else None
            alias_new = request.POST.get("alias_new") if request.POST.get("alias_new") else None
            try:
                minio_client.rename_object(
                    alias_old=f"{prefix}/{FOLDER_CAPTURED}/{alias_old}.{IMAGE_FORMAT}",
                    alias_new=f"{prefix}/{FOLDER_CAPTURED}/{alias_new}.{IMAGE_FORMAT}"
                )
                # generate JSON response (correct)
                return JsonResponse({"alias": alias_new})
            except:
                # generate JSON response (error)
                return JsonResponse({"error": "something went wrong"})
    # generate JSON response (error)
    return JsonResponse({"error": "you don't have enough permissions"})


def create_scoring_report(request, prefix: str):
    if request.method == "GET":
        if request.user.is_authenticated:
            if prefix:
                # create & return scoring report
                dh = DocHeader.objects.filter(is_active=True).first()
                data = {
                    "doc_header": dh.content if dh else "",
                    "subject_title": prefix.split("]")[1][1:],
                    "date": prefix.split("[")[-1][:-1],
                    "table_head": [
                        VerifiedWorkEntry._meta.get_field("unique_key").verbose_name,
                        VerifiedWorkEntry._meta.get_field("score").verbose_name,
                        VerifiedWorkEntry._meta.get_field("user").verbose_name,
                        _("Date verified")
                    ],
                    "qs": VerifiedWorkEntry.objects.filter(archive__prefix=prefix).order_by("-score")
                }
                # return render(request, template_name="docs/template_scoring_report.html", context=data)
                report = render_to_string(template_name="docs/template_scoring_report.html", context=data)
                response = HttpResponse(report, content_type="application/text charset=utf-8")
                response["Content-Disposition"] = 'attachment; filename="scoring_report.html"'
                return response

    # generate JSON response (error)
    return JsonResponse({"error": "you don't have enough permissions"})


def logout_user(request):
    logout(request)
    return redirect("auth")


# VALIDATORS & MODIFICATIONS ----------------------------------------------------------------------------------------- #
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


def modification_verified_work_entry(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            # get data from request
            alias = request.GET.get("alias") if request.GET.get("alias") else None
            # generate JSON response (correct / incorrect)
            try:
                minio_client.get_object_stats(alias=alias)
                return JsonResponse({"url": minio_client.get_object_url(alias=alias), "error": None})
            except S3Error:
                return JsonResponse({"url": None, "error": _("No image could be found as requested")})
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
