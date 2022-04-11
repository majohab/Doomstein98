from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='/accounts/login/')
def menu(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get menu 

    Returns:
        HTTP Response: Menu page
    """
    return render(request, 'menu.html', {})
