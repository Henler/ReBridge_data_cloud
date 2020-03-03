"""django-APIs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required

handler400 = 'rest_framework.exceptions.bad_request'
handler500 = 'rest_framework.exceptions.server_error'

urlpatterns = [
    path('table_cleaning/', include('table_cleaning.urls')),
    path('triangle_formatting/', include('triangle_formatting.urls')),
    path('admin/', admin.site.urls),
    # https://wsvincent.com/django-user-authentication-tutorial-login-and-logout/
    path('accounts/', include('django.contrib.auth.urls')),
    path('', login_required(TemplateView.as_view(template_name='home.html')), name='index'),
]