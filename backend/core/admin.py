from django.contrib import admin
from .models import products, orders, shipments


admin.site.register(products)
admin.site.register(orders)
admin.site.register(shipments)
# Register your models here.
