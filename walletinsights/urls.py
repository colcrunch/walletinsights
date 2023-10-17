from django.urls import re_path

from . import views

app_name = "walletinsights"

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^add_owner/$", views.add_owner, name="add_character"),
]
