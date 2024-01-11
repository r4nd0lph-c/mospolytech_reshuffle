from django.urls import path
from main.views import *

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("validation_part/", validation_part, name="validation_part"),
    path("validation_task/", validation_task, name="validation_task"),
]
