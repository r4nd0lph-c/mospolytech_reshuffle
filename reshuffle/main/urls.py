from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView
from main.views import *

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("main/img/favicons/favicon.ico"))),
    path("auth/", Auth.as_view(redirect_authenticated_user=True), name="auth"),
    path("", Index.as_view(), name="index"),
    path("creation/", Creation.as_view(), name="creation"),
    path("download/", Download.as_view(), name="download"),
    path("verification/", Verification.as_view(), name="verification"),
    path("verification/capture/<str:prefix>", Capture.as_view(), name="capture"),
    path("verification/score/<str:prefix>/<str:unique_key>", Score.as_view(), name="score"),
    path("download_archive/<str:prefix>", download_archive, name="download_archive"),
    path("verification/recognize", recognize, name="recognize"),
    path("logout/", logout_user, name="logout"),
    path("validation_part/", validation_part, name="validation_part"),
    path("validation_task/", validation_task, name="validation_task"),
]
