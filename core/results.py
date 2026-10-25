from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Assessment
from .offers import select_offers, snapshot_offers
from .repository import load_questionnaire
from .scoring import RULES_VERSION, calculate


@login_required
@require_POST
@transaction.atomic
def evaluate(request):
    get_user_model().objects.select_for_update().get(pk=request.user.pk)
    profile, finances = load_questionnaire(request.user)
    if not profile or not finances:
        messages.error(request, "Сначала заполните и сохраните анкету.")
        return redirect("questionnaire")
    result = calculate(
        finances.monthly_income,
        finances.current_payments,
        finances.requested_amount,
        profile.experience_months,
    )
    offers = select_offers(
        result.score,
        finances.monthly_income,
        finances.current_payments,
        finances.requested_amount,
        finances.term_months,
    )
    assessment = Assessment.objects.create(
        user=request.user,
        score=result.score,
        burden_amount=result.burden_amount,
        burden_percent=result.burden_percent,
        score_details=result.details,
        rules_version=RULES_VERSION,
        input_snapshot={
            "monthly_income": str(finances.monthly_income),
            "current_payments": str(finances.current_payments),
            "requested_amount": str(finances.requested_amount),
            "term_months": finances.term_months,
            "experience_months": profile.experience_months,
        },
        offers_snapshot=snapshot_offers(offers),
    )
    return redirect("result", pk=assessment.pk)


@login_required
@require_GET
def latest_result(request):
    assessment = Assessment.objects.filter(user=request.user).first()
    if assessment:
        return redirect("result", pk=assessment.pk)
    return render(request, "core/results_empty.html")


@login_required
@require_GET
def result(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    profile, finances = load_questionnaire(request.user)
    changed = bool(
        profile
        and finances
        and max(profile.updated_at, finances.updated_at) > assessment.created_at
    )
    return render(
        request,
        "core/results.html",
        {"assessment": assessment, "changed": changed, "score_width": assessment.score / 10},
    )
