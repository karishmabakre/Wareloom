from django.db import models
from django.utils import timezone

class products(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    supplier = models.CharField(
            max_length=200,
            default="Unknown Supplier"
        )
    location = models.CharField(max_length=200, default="Main Warehouse")
    reorder_level = models.IntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True,default='')
    image = models.ImageField(
    upload_to="products/",
    blank=True,
    null=True
)

    def __str__(self):
        return f"{self.name} - {self.price}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("Received", "Stock Received"),
        ("Dispatched", "Stock Dispatched"),
        ("Adjustment", "Manual Adjustment"),
        ("Return", "Stock Returned"),
    ]

    product = models.ForeignKey(
        products,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
    )

    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()

    quantity_changed = models.IntegerField()

    reason = models.CharField(max_length=255)

    performed_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.product.name}: "
            f"{self.previous_quantity} -> {self.new_quantity}"
        )


class orders(models.Model):

    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Picking', 'Picking'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    PAYMENT_METHODS = [
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Credit Card', 'Credit Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Wallet', 'Wallet'),
    ]
    SHIPPING_METHODS = [
        ('Standard Shipping', 'Standard Shipping'), 
        ('Express Shipping', 'Express Shipping'),
        ('Overnight Shipping', 'Overnight Shipping'),
    ]   
    
    order_number = models.CharField(max_length=20, unique=True)
    order_date = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)

    # Customer information
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)

    # Link to your existing Product model
    product = models.ForeignKey(
        'core.products',
        on_delete=models.PROTECT,
        related_name='customer_orders'
    )

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # Payment information
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
        default='Cash on Delivery'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='Pending'
    )

    # Shipping and tracking
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='Pending'
    )
    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_METHODS,
        default='Standard'
    )
    tracking_number = models.CharField(
        max_length=100, blank=True
    )
    shipped_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class shipments(models.Model):

    STATUS_CHOICES = [
        ('Preparing', 'Preparing'),
        ('Shipped', 'Shipped'),
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Delayed', 'Delayed'),
    ]

    shipment_id = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(
        orders,
        on_delete=models.CASCADE,
        related_name='shipment'
    )
    tracking_number = models.CharField(max_length=100)
    carrier = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Preparing'
    )
    shipment_date = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return f"{self.shipment_id} - {self.status}"


