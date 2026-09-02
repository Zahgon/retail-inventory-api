"""
URL configuration.

Patterns are listed in the order the API resolves them, which is part of the
observable behaviour:

* The documentation surface is matched first.
* ``products/total_value`` and ``products/search`` are matched before
  ``products/<product_id>``, so those two literal paths win over the detail
  route instead of being parsed as identifiers.
* Identifiers are captured as ``str`` rather than ``uuid`` so that a malformed
  identifier reaches the view and is reported as a validation error, instead of
  failing to match and being reported as a missing resource.

``handler404`` also implements the trailing-slash redirect, which is why
``APPEND_SLASH`` is switched off in the settings.
"""

from django.urls import path

from . import views

handler404 = "app.core.routing.not_found"

urlpatterns = [
    path("openapi.json", views.openapi),
    path("docs", views.docs),
    path("docs/oauth2-redirect", views.oauth2_redirect),
    path("redoc", views.redoc),
    path("health", views.health),
    path("", views.home),
    path("products/total_value", views.inventory_value),
    path("products/", views.products),
    path("products/search", views.product_search),
    path("products/<str:product_id>", views.product_detail),
    path("products/<str:product_id>/variants", views.product_variants),
    path("products/<str:product_id>/variants/<str:variant_id>", views.variant_detail),
]
