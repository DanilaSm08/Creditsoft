from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .accounts import register
from .forms import LoginForm
from .questionnaire import questionnaire
from .views import health

urlpatterns = [
    path("", questionnaire, name="questionnaire"),
    path("accounts/register/", register, name="register"),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="core/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("health/", health, name="health"),
]
