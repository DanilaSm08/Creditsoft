"""Catalogue selection; inclusive conditions, stable order by rate then id."""

from .models import LoanOffer


def select_offers(score, monthly_income, current_payments, requested_amount, term_months):
    # Use unrounded burden so values above a threshold cannot qualify by rounding.
    burden = current_payments / monthly_income * 100
    return LoanOffer.objects.filter(
        active=True,
        min_score__lte=score,
        max_burden__gte=burden,
        min_amount__lte=requested_amount,
        max_amount__gte=requested_amount,
        min_term__lte=term_months,
        max_term__gte=term_months,
    ).order_by("annual_rate", "pk")


def snapshot_offers(offers):
    return [
        {
            "id": offer.pk,
            "name": offer.name,
            "logo": offer.logo,
            "annual_rate": str(offer.annual_rate),
            "min_amount": str(offer.min_amount),
            "max_amount": str(offer.max_amount),
            "min_term": offer.min_term,
            "max_term": offer.max_term,
        }
        for offer in offers
    ]
