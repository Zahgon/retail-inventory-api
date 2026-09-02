from .analytics import inventory_value
from .docs import docs, oauth2_redirect, openapi, redoc
from .health import health
from .home import home
from .products import product_detail, product_search, products
from .variants import product_variants, variant_detail

__all__ = [
    "openapi",
    "docs",
    "oauth2_redirect",
    "redoc",
    "health",
    "home",
    "inventory_value",
    "products",
    "product_search",
    "product_detail",
    "product_variants",
    "variant_detail",
]
