"""
URL configuration for ngo_ccsh project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="index"),
    path('api-auth/', include('rest_framework.urls')),  # para fazer login na browsable API do DRF
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("despesas/", include("despesas.urls")),
    path("parciais/", include("parciais.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
