import pytest
from django.contrib.auth.models import User
from django.test import Client, TestCase


@pytest.mark.requirement("CR-01.1", "CR-01.2", "CR-01.3")
class AccountTests(TestCase):
    def test_registration_hashes_password_and_creates_session(self):
        password = "StudyPassword!4581"
        response = self.client.post(
            "/accounts/register/",
            {"username": "borrower", "password1": password, "password2": password},
        )
        self.assertRedirects(response, "/")
        user = User.objects.get(username="borrower")
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_and_password_validation(self):
        User.objects.create_user("borrower", password="StudyPassword!4581")
        response = self.client.post(
            "/accounts/register/", {"username": "borrower", "password1": "123", "password2": "456"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertIn("password2", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_failure_success_logout_and_protected_page(self):
        User.objects.create_user("borrower", password="StudyPassword!4581")
        self.assertRedirects(self.client.get("/"), "/accounts/login/?next=/")
        response = self.client.post(
            "/accounts/login/", {"username": "borrower", "password": "incorrect"}
        )
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertRedirects(
            self.client.post(
                "/accounts/login/", {"username": "borrower", "password": "StudyPassword!4581"}
            ),
            "/",
        )
        self.assertRedirects(self.client.get("/accounts/register/"), "/")
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
        self.assertRedirects(self.client.post("/accounts/logout/"), "/accounts/login/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registration_requires_csrf(self):
        browser = Client(enforce_csrf_checks=True)
        self.assertEqual(browser.post("/accounts/register/", {"username": "x"}).status_code, 403)

    def test_auth_pages_and_unsupported_method(self):
        self.assertContains(self.client.get("/accounts/register/"), "Регистрация")
        self.assertEqual(self.client.put("/accounts/register/").status_code, 405)

    def test_login_ignores_external_redirect(self):
        User.objects.create_user("borrower", password="StudyPassword!4581")
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "borrower",
                "password": "StudyPassword!4581",
                "next": "https://example.com/",
            },
        )
        self.assertRedirects(response, "/")
