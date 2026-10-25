from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import FinanceForm, ProfileForm
from .repository import load_questionnaire, save_questionnaire


@login_required
@require_http_methods(["GET", "POST"])
def questionnaire(request):
    profile, finances = load_questionnaire(request.user)
    data = request.POST if request.method == "POST" else None
    profile_form = ProfileForm(data, instance=profile)
    finance_form = FinanceForm(data, instance=finances)
    if request.method == "POST":
        profile_valid, finance_valid = profile_form.is_valid(), finance_form.is_valid()
        if profile_valid and finance_valid:
            save_questionnaire(request.user, profile_form, finance_form)
            messages.success(request, "Анкета сохранена.")
            return redirect("questionnaire")
    return render(
        request,
        "core/questionnaire.html",
        {"profile_form": profile_form, "finance_form": finance_form, "saved": profile is not None},
    )
