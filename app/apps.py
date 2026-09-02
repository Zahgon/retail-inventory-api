"""
Application registry entry for the Retail Inventory API.

The models of this project are SQLModel classes rather than Django models, so
the app config exists only to give Django a well-named application to load.
"""

from django.apps import AppConfig


class RetailInventoryConfig(AppConfig):
    name = "app"
    verbose_name = "Retail Inventory API"
