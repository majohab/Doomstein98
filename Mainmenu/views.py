from django.shortcuts import render

# Create your views here.

def menu(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get menu page.

    Returns:
        HTTP Response: Menu page
    """
    return render(request, 'menu.html', {})

def play(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get start page.

    Returns:
        HTTP Response: Start page
    """
    return render(request, 'play.html', {})

    
def impressum(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get impressum page.

    Returns:
        HTTP Response: Impressum page
    """
    return render(request, 'impressum.html', {})