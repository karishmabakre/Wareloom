"""
URL configuration for warehouse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("products/", views.product_crud, name="products"),
    path("orders/", views.order_crud, name="orders"),
    path("shipments/", views.shipments_view, name="shipments"),

    path("api/products/", views.product_api, name="product_api"),
    path(
        "api/products/<int:product_id>/",
        views.product_detail_api,
        name="product_detail_api",
    ),

    path("api/orders/", views.order_api, name="order_api"),
    path("api/orders/<int:order_id>/",views.order_detail_api,name="order_detail_api",
    ),

    path("api/shipments/", views.shipment_api, name="shipment_api"),
    path(
        "api/shipments/<int:shipment_pk>/",
        views.shipment_detail_api,
        name="shipment_detail_api",
    ),
    path("analytics/", views.analytics_view, name="analytics"),
    path("contact/", views.contact_view, name="contact"),
    path("expiry-rescue/", views.expiry_rescue, name="expiry_rescue"),
    path("stock-sense/", views.stock_sense, name="stock_sense"),
    path("inventory-time-machine/", views.inventory_time_machine, name="inventory_time_machine"),
    
path(
    "reports-alerts/",
    views.reports_alerts,
    name="reports_alerts",
),

path(
    "reports/export/<str:report_type>/",
    views.export_report_csv,
    name="export_report_csv",
),

]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )