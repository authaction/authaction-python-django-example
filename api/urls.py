from django.urls import path

from api.views import protected_view, public_view

urlpatterns = [
    path("public", public_view),
    path("protected", protected_view),
]
