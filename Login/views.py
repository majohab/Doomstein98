from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.conf import settings
from threading import Thread
from .utils import generate_token
from Login.forms import RegistrationForm, UserLoginForm
from .models import User

# Create your views here.
def play(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get start page.

    Returns:
        HTTP Response: Start page
    """
    return render(request, 'play.html', {})

def dashboard(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get user dashboard

    Returns:
        HTTP Response: Dashboard
    """
    return render(request, 'dashboard.html', {})

@login_required(login_url='/accounts/login/')
def menu(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get menu 

    Returns:
        HTTP Response: Menu page
    """
    return render(request, 'menu.html', {})

class EmailThread(Thread):
    """Sends verification email to user.

    Args:
        Thread (Class): Inherits Thread class.
    """
    def __init__(self, email):
        self.email = email
        Thread.__init__(self)

    def run(self):
        self.email.send()

def send_activation_email(user, request):
    """Create verification email and send it.

    Args:
        user (User): User to send email to.
        request (GET): Request to get email.
    """
    current_site = get_current_site(request)
    email_subject = 'Activate your account'
    email_body = render_to_string('registration/activation/activate.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body,
                         from_email=settings.EMAIL_FROM_USER,
                         to=[user.email]
                         )

    EmailThread(email).start()

def activate_user(request, uidb64, token):
    """Activate the created user account.

    Args:
        request (GET): Get HTML page.
        uidb64 (uidb64): Encrypted user identification
        token (Token): Verification token

    Returns:
        HTTP Response: Login page
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))

        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.add_message(request, messages.SUCCESS,
                             'Email verified, you can now login')
        return redirect(reverse('login'))

    messages.add_message(request, messages.ERROR,
                             'Email verification failed.')
    return render(request, 'registration/activation/login.html', {"user": user})

def registerUser(request):
    """Form to register User and create account.

    Args:
        request (GET): HTML page

    Returns:
        HTTP Response: Registration form
    """
    context = {}
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_activation_email(user, request)
            messages.add_message(request, messages.SUCCESS,
                                 'We sent you an email to verify your account.')
            return redirect(reverse("login"))
        else:
            context['registration_form'] = form
            messages.add_message(request, messages.ERROR,
                                 'User was not created. Please enter valid credentials.')
    else:
        form = RegistrationForm(request)
        context['registration_form'] = form
    return render(request, "registration/register.html",
                  {"form": RegistrationForm})

def loginUser(request):
    """Form to log user in.

    Args:
        request (GET): Get HTML page

    Returns:
        HTTP Response: Login form
    """
    context = {"form": UserLoginForm}
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data.get('username'), 
                                password=form.cleaned_data.get('password'))
            login(request, user)
            return redirect(reverse("menu"))
        else:
            user = authenticate(request, username=form.cleaned_data.get('username'),
                                password=form.cleaned_data.get('password'))
            
            if not user: 
                messages.add_message(request, messages.ERROR,
                                 'Please enter valid credentials or activate your account.')
                context['user_login_form'] = form
                return render(request, "registration/login.html",
                              context)
 
            #Todo: is_activate does not work.
            if not user.is_active:
                messages.add_message(request, messages.ERROR,
                                 'Please activate your account.')
                context['user_login_form'] = form
                return render(request, "registration/login.html",
                              context)   
    else:
        form = UserLoginForm(request)
        context['user_login_form'] = form
    return render(request, "registration/login.html",
                  context)