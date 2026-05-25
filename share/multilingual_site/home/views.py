from django.shortcuts import render
from django.utils.translation import gettext as _

def index(request):
    context = {
        "welcome_message": _("Hello, welcome to my multilingual site!"),
        "choose_language": _("Choose your language"),
    }
    return render(request, "home/index.html", context)

