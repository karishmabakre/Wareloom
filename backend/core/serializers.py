
from rest_framework import serializers
from .models import products, orders, shipments


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = products
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    class Meta:
        model = orders
        fields = "__all__"


class ShipmentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source="order.order_number",
        read_only=True
    )
    customer_name = serializers.CharField(
        source="order.customer_name",
        read_only=True
    )

    class Meta:
        model = shipments
        fields = "__all__"
