from base64 import urlsafe_b64encode

from django import forms
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template import loader
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes

from apps.users.generators import ChangeEmailTokenGenerator, ConfirmEmailTokenGenerator
from apps.users.models import CustomUser
from config.form_class import FormClass
from config.mixins import OptsUser, OptsUserInstance


class Login(FormClass, OptsUser, AuthenticationForm):
    title = "Login"
    submit = "Login"
    bottom = "users/login.html"
    success = settings.LOGIN_REDIRECT_URL

    def init(self):
        self.fields["username"].label = "E-Mail"

    def inject_request(self, request: HttpRequest):
        self.request = request  # type: ignore

    def ok(self):
        auth_login(self.request, self.get_user())
        return self.get_user().pk


class ChangePassword(FormClass, PasswordChangeForm):
    addons = {"navs": ["settings"]}
    submit = "Change"
    success = reverse_lazy("change_password_done")

    def __init__(self, user, opts, *args, **kwargs):
        self.user = user
        self.opts = opts
        super().__init__(user, *args, **kwargs)

    def send_mail(self, user: CustomUser):
        subject = "Dein Passwort wurde geändert"
        body = loader.render_to_string("users/emails/change_password_3_email.txt", {})
        email_message = EmailMultiAlternatives(
            subject, body, settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        html_email = loader.render_to_string(
            "users/emails/change_password_3_email.html", {}
        )
        email_message.attach_alternative(html_email, "text/html")
        email_message.send()

    def ok(self):
        user = super().save()
        assert isinstance(user, CustomUser)
        self.send_mail(user)
        return user.pk


class ChangeEmail(FormClass, OptsUserInstance[CustomUser], forms.ModelForm):
    addons = {"navs": ["settings"]}
    title = "Change E-Mail"
    success = reverse_lazy("change_email_done")

    class Meta:
        model = CustomUser
        fields = ["new_email"]

    def inject_request(self, request: HttpRequest):
        self.request = request

    def get_instance(self) -> CustomUser:
        assert isinstance(self.user, CustomUser)
        return self.user

    def send_email_change_mail(self, request, user):
        token = ChangeEmailTokenGenerator().make_token(user)
        current_site = get_current_site(request)
        uid = urlsafe_b64encode(force_bytes(user.pk)).decode()
        url = reverse_lazy(
            "change_email_confirm", kwargs={"uidb64": uid, "token": token}
        )
        protocol = "https" if request.is_secure() else "http"
        link = f"{protocol}://{current_site}{url}"
        subject = "Confirm your new email"

        context = {"link": link}
        body = loader.render_to_string(
            "users/emails/change_email_3_email_send.txt", context
        )

        email_message = EmailMultiAlternatives(
            subject, body, settings.DEFAULT_FROM_EMAIL, [user.new_email]
        )
        html_email = loader.render_to_string(
            "users/emails/change_email_3_email_send.html", context
        )
        email_message.attach_alternative(html_email, "text/html")

        email_message.send()

    def ok(self):
        user: CustomUser = super().save()
        try:
            self.send_email_change_mail(self.request, user)
        except Exception as e:
            user.new_email = None
            user.save()
            raise e
        return user.pk


class Register(FormClass, OptsUser, UserCreationForm):
    submit = "Register"
    title = "Register"
    bottom = "users/register_user_1.html"
    success = reverse_lazy("register_user_done")

    class Meta:
        model = CustomUser
        fields = ("email", "password1", "password2")

    def init(self) -> None:
        self.fields["email"].widget.attrs = {"autocomplete": "email"}

    def inject_request(self, request: HttpRequest):
        self.request = request

    def send_activation_mail(self, request, user):
        token = ConfirmEmailTokenGenerator().make_token(user)
        current_site = get_current_site(request)
        uid = urlsafe_b64encode(force_bytes(user.pk)).decode()
        url = reverse_lazy(
            "register_confirm_email", kwargs={"uidb64": uid, "token": token}
        )
        protocol = "https" if request.is_secure() else "http"
        link = f"{protocol}://{current_site}{url}"
        subject = "Confirm your email"

        context = {"link": link}
        body = loader.render_to_string(
            "users/emails/register_user_3_email_send.txt", context
        )
        email_message = EmailMultiAlternatives(
            subject, body, settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        html_email = loader.render_to_string(
            "users/emails/register_user_3_email_send.html", context
        )
        email_message.attach_alternative(html_email, "text/html")
        email_message.send()

    def ok(self):
        user: CustomUser = super().save(commit=False)
        user.save()
        try:
            self.send_activation_mail(self.request, user)
        except Exception as e:
            user.delete()
            raise e
        return user.pk


class ResetPassword(FormClass, OptsUser, PasswordResetForm):
    title = "Reset Password"
    text = "Please type in your email and we will send a password reset email."
    success = reverse_lazy("password_reset_done")

    def inject_request(self, request: HttpRequest):
        self.request = request

    def ok(self):
        self.save(request=self.request)  # type: ignore
        return 0


class SetPassword(FormClass, SetPasswordForm):
    title = "Set Password"
    success = reverse_lazy("password_reset_complete")
