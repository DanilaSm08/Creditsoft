from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import LoanOffer

CATALOGUE = [
    ("Север · Стандарт", "north", "12.90", 850, "30", 50000, 1000000, 12, 60),
    ("Ось · Оптимум", "axis", "15.50", 700, "40", 10000, 2000000, 6, 84),
    ("Горизонт · Универсальный", "horizon", "18.90", 550, "50", 10000, 3000000, 6, 84),
    ("Пульс · Доступный", "pulse", "24.00", 350, "70", 10000, 500000, 6, 60),
]


class Command(BaseCommand):
    help = "Create/update four explicitly fictional educational loan offers."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, logo, rate, score, burden, minimum, maximum, first_term, last_term in CATALOGUE:
            LoanOffer.objects.update_or_create(
                name=name,
                defaults={
                    "logo": logo,
                    "annual_rate": Decimal(rate),
                    "min_score": score,
                    "max_burden": Decimal(burden),
                    "min_amount": minimum,
                    "max_amount": maximum,
                    "min_term": first_term,
                    "max_term": last_term,
                    "active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Демонстрационный каталог: 4 предложения."))
