from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import BorrowerProfile, FinancialData


class AccessibleForm:
    def style_fields(self):
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["aria-describedby"] = f"id_{name}_hint id_{name}_errors"


class RegistrationForm(AccessibleForm, UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["username"].help_text = "Буквы, цифры и символы @ . + - _."
        self.style_fields()


class LoginForm(AccessibleForm, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.style_fields()


class ProfileForm(AccessibleForm, forms.ModelForm):
    class Meta:
        model = BorrowerProfile
        fields = (
            "full_name",
            "birth_date",
            "passport_series",
            "passport_number",
            "employer",
            "experience_months",
        )
        widgets = {
            "birth_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "passport_series": forms.TextInput(
                attrs={"inputmode": "numeric", "autocomplete": "off"}
            ),
            "passport_number": forms.TextInput(
                attrs={"inputmode": "numeric", "autocomplete": "off"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d", "%d.%m.%Y"]
        self.fields["experience_months"].help_text = "0, если нет текущего места работы."
        self.fields["employer"].help_text = "Укажите «Не работаю», если не трудоустроены."
        self.style_fields()

    def clean(self):
        data = super().clean()
        birth_date, experience = data.get("birth_date"), data.get("experience_months")
        if birth_date and experience is not None:
            today = timezone.localdate()
            possible = max(
                0,
                (today.year - birth_date.year - 18) * 12
                + today.month
                - birth_date.month
                - (today.day < birth_date.day),
            )
            if experience > possible:
                self.add_error(
                    "experience_months", "Стаж не может превышать время с совершеннолетия."
                )
        return data


class FinanceForm(AccessibleForm, forms.ModelForm):
    class Meta:
        model = FinancialData
        fields = ("monthly_income", "current_payments", "requested_amount", "term_months")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["monthly_income"].help_text = "Общий доход после уплаты налогов за месяц."
        self.fields[
            "current_payments"
        ].help_text = "Сумма ежемесячных платежей. Если кредитов нет, укажите 0."
        self.fields["requested_amount"].help_text = "От 10 000 до 5 000 000 ₽."
        self.fields["term_months"].help_text = "От 6 до 84 месяцев."
        self.style_fields()
