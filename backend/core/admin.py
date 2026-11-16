from django.contrib import admin
from .models import UserProfile, products, orders, shipments


admin.site.register(products)
admin.site.register(orders)
admin.site.register(shipments)
# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__username", "user__email")