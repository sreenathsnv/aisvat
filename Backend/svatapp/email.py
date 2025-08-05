from djoser import email
from django.template.loader import render_to_string

class ActivationEmail(email.ActivationEmail):
    template_name = 'email/activation_email.html'


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'password_reset.html'