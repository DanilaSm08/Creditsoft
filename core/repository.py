"""Atomic ownership-scoped persistence through Django ORM."""

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import BorrowerProfile, FinancialData


def load_questionnaire(user):
    return (
        BorrowerProfile.objects.filter(user=user).first(),
        FinancialData.objects.filter(user=user).first(),
    )


@transaction.atomic
def save_questionnaire(user, profile_form, finance_form):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    profile = profile_form.save(commit=False)
    finances = finance_form.save(commit=False)
    profile.user = finances.user = user
    profile.full_clean()
    finances.full_clean()
    profile.save()
    finances.save()
    return profile, finances
