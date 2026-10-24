import csv
import json

from decimal import Decimal, InvalidOperation
from datetime import timedelta
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import (
    Sum, F, Q, DecimalField, ExpressionWrapper,Count
)
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import products, orders, shipments,StockMovement
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    ShipmentSerializer,
)
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods


# =========================================================
# HOME, AUTHENTICATION AND LOGOUT
# =========================================================

def home(request):
    total_products = products.objects.count()

    inventory_units = products.objects.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    # Real order data
    total_orders = orders.objects.count()

    # Real shipment data
    total_shipments = shipments.objects.count()

    context = {
        "total_products": total_products,
        "inventory_units": inventory_units,
        "total_orders": total_orders,
        "total_shipments": total_shipments,
    }
    return render(request,"index.html",context)


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user_obj = User.objects.filter(email__iexact=email).first()

        if user_obj is None:
            return render(request, "login.html", {
                "error_message": "Invalid email or password."
            })

        user = authenticate(
            request,
            username=user_obj.username,
            password=password,
        )

        if user is not None:
            login(request, user)
            request.session["username"] = user.username
            return redirect("dashboard")

        return render(request, "login.html", {
            "error_message": "Invalid email or password."
        })

    return render(request, "login.html")


def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get("firstName", "").strip()
        last_name = request.POST.get("lastName", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not first_name or not email or not password:
            return render(request, "signup.html", {
                "error_message": "Name, email and password are required."
            })

        if User.objects.filter(email__iexact=email).exists():
            return render(request, "signup.html", {
                "error_message": "Email already exists."
            })

        username = email.split("@")[0]
        base_username = username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )

        login(request, user)
        request.session["username"] = user.username
        return redirect("dashboard")

    return render(request, "signup.html")


def logout_view(request):
    logout(request)
    return redirect("home")


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):
    inventory_units = products.objects.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    inventory_value_expression = ExpressionWrapper(
        F("quantity") * F("price"),
        output_field=DecimalField(max_digits=16, decimal_places=2),
    )

    inventory_value = products.objects.aggregate(
        total=Sum(inventory_value_expression)
    )["total"] or Decimal("0.00")

    total_orders = orders.objects.count()
    pending_orders = orders.objects.filter(
        order_status="Pending"
    ).count()

    total_order_value = orders.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0.00")

    context = {
        "username": request.session.get("username", request.user.username),

        "total_products": products.objects.count(),
        "inventory_units": inventory_units,
        "inventory_value": inventory_value,
        "low_stock": products.objects.filter(
            quantity__lte=F("reorder_level")
        ).count(),
        "recent_products": products.objects.order_by("-id")[:5],

        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_order_value": total_order_value,
        "recent_orders": orders.objects.select_related(
            "product"
        ).order_by("-order_date")[:5],

        "total_shipments": shipments.objects.count(),
        "pending_shipments": shipments.objects.filter(
            status="Preparing"
        ).count(),
        "in_transit_shipments": shipments.objects.filter(
            status="In Transit"
        ).count(),
        "delivered_shipments": shipments.objects.filter(
            status="Delivered"
        ).count(),
        "recent_shipments": shipments.objects.select_related(
            "order"
        ).order_by("-shipment_date")[:5],
    }

    return render(request, "dashboard.html", context)


# =========================================================
# PRODUCT PAGE CRUD
# =========================================================

@login_required
def product_crud(request):
    if request.method == "POST":
        action = request.POST.get("action")

        
        # ---------------- CREATE PRODUCT ----------------
        if action == "create":
            try:
                product = products.objects.create(
                    name=request.POST.get("name", "").strip(),
                    sku=request.POST.get("sku", "").strip(),
                    category=request.POST.get("category", "").strip(),
                    quantity=int(request.POST.get("quantity", 0)),
                    price=int(request.POST.get("price", 0)),
                    supplier=request.POST.get(
                        "supplier", "Unknown Supplier"
                    ).strip() or "Unknown Supplier",
                    location=request.POST.get(
                        "location", "Main Warehouse"
                    ).strip() or "Main Warehouse",
                    reorder_level=int(
                        request.POST.get("reorder_level", 10)
                    ),
                    expiry_date=(
                        parse_date(request.POST.get("expiry_date", ""))
                        if request.POST.get("expiry_date")
                        else None
                    ),
                    manufacturing_date=(
                        parse_date(
                            request.POST.get("manufacturing_date", "")
                        )
                        if request.POST.get("manufacturing_date")
                        else None
                    ),
                    description=request.POST.get(
                        "description", ""
                    ).strip(),
                    image=request.FILES.get("image"),
                )

                # Record initial stock in Inventory Time Machine
                if product.quantity > 0:
                    StockMovement.objects.create(
                        product=product,
                        movement_type="Received",
                        previous_quantity=0,
                        new_quantity=product.quantity,
                        quantity_changed=product.quantity,
                        reason="Initial stock when product was created",
                        performed_by=request.user,
                    )

                messages.success(
                    request, "Product created successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request, "Enter valid product values."
                )
            except IntegrityError:
                messages.error(
                    request, "Could not create this product."
                )

            return redirect("products")

        # ---------------- UPDATE PRODUCT ----------------
        elif action == "update":
            product = get_object_or_404(
                products,
                pk=request.POST.get("product_id")
            )

            try:
                product.name = request.POST.get("name", "").strip()
                product.sku = request.POST.get("sku", "").strip()
                product.category = request.POST.get(
                    "category", ""
                ).strip()
                product.quantity = int(
                    request.POST.get("quantity", 0)
                )
                product.price = int(
                    request.POST.get("price", 0)
                )
                product.supplier = request.POST.get(
                    "supplier", "Unknown Supplier"
                ).strip() or "Unknown Supplier"
                product.location = request.POST.get(
                    "location", "Main Warehouse"
                ).strip() or "Main Warehouse"
                product.reorder_level = int(
                    request.POST.get("reorder_level", 10)
                )

                product.expiry_date = (
                    parse_date(request.POST.get("expiry_date", ""))
                    if request.POST.get("expiry_date")
                    else None
                )

                product.manufacturing_date = (
                    parse_date(
                        request.POST.get("manufacturing_date", "")
                    )
                    if request.POST.get("manufacturing_date")
                    else None
                )

                product.description = request.POST.get(
                    "description", ""
                ).strip()

                # Keep the existing image if no new image is uploaded.
                uploaded_image = request.FILES.get("image")
                if uploaded_image:
                    product.image = uploaded_image

                product.save()

                messages.success(
                    request, "Product updated successfully."
                )

            except (ValueError, TypeError):
                messages.error(
                    request, "Enter valid product values."
                )
            except IntegrityError:
                messages.error(
                    request, "Could not update this product."
                )

            return redirect("products")

        # ---------------- DELETE PRODUCT ----------------
        elif action == "delete":
            product = get_object_or_404(
                products,
                pk=request.POST.get("product_id")
            )

            try:
                product.delete()
                messages.success(
                    request, "Product deleted successfully."
                )
            except IntegrityError:
                messages.error(
                    request,
                    "This product is linked to an order "
                    "and cannot be deleted."
                )

            return redirect("products")

        else:
            messages.error(request, "Invalid product action.")
            return redirect("products")

    # ---------------- LIST PRODUCTS + PAGINATION ----------------
    product_list = products.objects.all().order_by("-id")

    paginator = Paginator(product_list, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products.html",
        {
            "products": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
        },
    )


# =========================================================
# PRODUCT REST API
# =========================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def product_api(request):
    if request.method == "GET":
        queryset = products.objects.all().order_by("-id")
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    serializer = ProductSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def product_detail_api(request, product_id):
    product = get_object_or_404(products, pk=product_id)

    if request.method == "GET":
        return Response(ProductSerializer(product).data)

    if request.method in ("PUT", "PATCH"):
        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=(request.method == "PATCH"),
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        product.delete()
    except IntegrityError:
        return Response(
            {"detail": "Product is linked to an order and cannot be deleted."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================
# ORDER PAGE CRUD
# =========================================================


@login_required
def order_crud(request):

    # =====================================================
    # CREATE / UPDATE / DELETE
    # =====================================================
    if request.method == "POST":
        action = request.POST.get("action")
        order_pk = request.POST.get("order_pk")

        if action in ("create", "update"):
            order = (
                get_object_or_404(orders, pk=order_pk)
                if action == "update"
                else orders()
            )

            order_number = request.POST.get(
                "order_number", ""
            ).strip()

            if not order_number:
                messages.error(request, "Order number is required.")
                return redirect("orders")

            duplicate = orders.objects.filter(
                order_number=order_number
            ).exclude(pk=order.pk if order.pk else None).exists()

            if duplicate:
                messages.error(
                    request, "This order number already exists."
                )
                return redirect("orders")

            try:
                product = get_object_or_404(
                    products, pk=request.POST.get("product")
                )

                quantity = int(request.POST.get("quantity", 0))
                unit_price = Decimal(
                    request.POST.get("unit_price", "0")
                )

                if quantity < 1:
                    raise ValueError(
                        "Quantity must be at least 1."
                    )

                if unit_price < 0:
                    raise ValueError(
                        "Unit price cannot be negative."
                    )

                with transaction.atomic():
                    order.order_number = order_number

                    order.customer_name = request.POST.get(
                        "customer_name", ""
                    ).strip()

                    order.customer_email = request.POST.get(
                        "customer_email", ""
                    ).strip()

                    order.customer_phone = request.POST.get(
                        "customer_phone", ""
                    ).strip()

                    order.shipping_address = request.POST.get(
                        "shipping_address", ""
                    ).strip()

                    order.city = request.POST.get(
                        "city", ""
                    ).strip()

                    order.pin_code = request.POST.get(
                        "pin_code", ""
                    ).strip()

                    order.product = product
                    order.quantity = quantity
                    order.unit_price = unit_price

                    # Recalculate the total using the submitted
                    # quantity and unit price.
                    order.total_amount = quantity * unit_price

                    order.payment_method = request.POST.get(
                        "payment_method", "Cash on Delivery"
                    )

                    order.payment_status = request.POST.get(
                        "payment_status", "Pending"
                    )

                    order.order_status = request.POST.get(
                        "order_status", "Pending"
                    )

                    order.shipping_method = request.POST.get(
                        "shipping_method", "Standard Shipping"
                    )

                    order.tracking_number = request.POST.get(
                        "tracking_number", ""
                    ).strip()

                    # Parse optional date fields.
                    for field in (
                        "expected_delivery_date",
                        "shipped_date",
                        "delivered_date",
                    ):
                        raw_date = request.POST.get(field, "")
                        parsed_date = (
                            parse_date(raw_date) if raw_date else None
                        )

                        if raw_date and parsed_date is None:
                            raise ValueError(
                                f"Invalid date for {field.replace('_', ' ')}."
                            )

                        setattr(order, field, parsed_date)

                    # Parse order datetime if supplied.
                    raw_order_date = request.POST.get(
                        "order_date", ""
                    )

                    if raw_order_date:
                        parsed_datetime = parse_datetime(
                            raw_order_date
                        )

                        if parsed_datetime is None:
                            raise ValueError(
                                "Invalid order date and time."
                            )

                        if timezone.is_naive(parsed_datetime):
                            parsed_datetime = timezone.make_aware(
                                parsed_datetime,
                                timezone.get_current_timezone(),
                            )

                        order.order_date = parsed_datetime

                    order.save()

                messages.success(
                    request,
                    "Order created successfully."
                    if action == "create"
                    else "Order updated successfully.",
                )

            except (ValueError, TypeError, InvalidOperation) as exc:
                messages.error(
                    request,
                    str(exc) or "Enter valid order values.",
                )

            except IntegrityError:
                messages.error(
                    request,
                    "Could not save order. Check its number "
                    "and required fields.",
                )

            return redirect("orders")

        elif action == "delete":
            order = get_object_or_404(
                orders, pk=order_pk
            )

            try:
                order.delete()
                messages.success(
                    request, "Order deleted successfully."
                )
            except IntegrityError:
                messages.error(
                    request,
                    "This order cannot be deleted because it "
                    "is linked to other records.",
                )

            return redirect("orders")

        else:
            messages.error(request, "Invalid order action.")
            return redirect("orders")

    # =====================================================
    # SEARCH + STATUS FILTERING
    # =====================================================
    queryset = orders.objects.select_related(
        "product"
    ).order_by("-order_date", "-pk")

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    edit_id = request.GET.get("edit")

    if search_query:
        queryset = queryset.filter(
            Q(order_number__icontains=search_query)
            | Q(customer_name__icontains=search_query)
            | Q(customer_email__icontains=search_query)
            | Q(customer_phone__icontains=search_query)
            | Q(product__name__icontains=search_query)
        )

    valid_order_statuses = {
        value for value, label in orders.ORDER_STATUS
    }

    if status_filter in valid_order_statuses:
        queryset = queryset.filter(
            order_status=status_filter
        )
    else:
        status_filter = ""

    # =====================================================
    # EDIT ORDER
    # =====================================================
    edit_order = None

    if edit_id:
        edit_order = get_object_or_404(
            orders, pk=edit_id
        )

    # =====================================================
    # SUMMARY STATISTICS
    # =====================================================
    total_order_value = (
        orders.objects.aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0.00")
    )

    # =====================================================
    # PAGINATION — 10 ORDERS PER PAGE
    # =====================================================
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    # =====================================================
    # TEMPLATE CONTEXT
    # =====================================================
    context = {
        "orders": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,

        "products": products.objects.all().order_by("name"),
        "edit_order": edit_order,

        "search_query": search_query,
        "status_filter": status_filter,

        "total_orders": orders.objects.count(),

        "pending_orders": orders.objects.filter(
            order_status="Pending"
        ).count(),

        "delivered_orders": orders.objects.filter(
            order_status="Delivered"
        ).count(),

        "total_order_value": total_order_value,

        "order_status_choices": orders.ORDER_STATUS,
        "payment_status_choices": orders.PAYMENT_STATUS,
        "payment_method_choices": orders.PAYMENT_METHODS,
        "shipping_method_choices": orders.SHIPPING_METHODS,
    }

    return render(
        request,
        "orders.html",
        context,
    )


# =========================================================
# ORDER REST API
# =========================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def order_api(request):
    if request.method == "GET":
        queryset = orders.objects.select_related("product").order_by("-order_date")

        search = request.query_params.get("q", "").strip()
        status_filter = request.query_params.get("status", "").strip()

        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search)
                | Q(customer_name__icontains=search)
                | Q(customer_email__icontains=search)
                | Q(product__name__icontains=search)
            )

        if status_filter in {v for v, _ in orders.ORDER_STATUS}:
            queryset = queryset.filter(order_status=status_filter)

        return Response(OrderSerializer(queryset, many=True).data)

    serializer = OrderSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if serializer.validated_data["quantity"] < 1:
        return Response(
            {"quantity": ["Quantity must be at least 1."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            order = serializer.save()
    except IntegrityError:
        return Response(
            {"detail": "Order number must be unique."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        OrderSerializer(order).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def order_detail_api(request, order_id):
    order = get_object_or_404(
        orders.objects.select_related("product"),
        pk=order_id,
    )

    if request.method == "GET":
        return Response(OrderSerializer(order).data)

    if request.method in ("PUT", "PATCH"):
        serializer = OrderSerializer(
            order,
            data=request.data,
            partial=(request.method == "PATCH"),
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            saved_order = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Could not update the order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(OrderSerializer(saved_order).data)

    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================
# SHIPMENT PAGE CRUD
# =========================================================

@login_required
def shipments_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        shipment_pk = request.POST.get("shipment_pk")

        if action == "delete":
            shipment = get_object_or_404(shipments, pk=shipment_pk)
            shipment.delete()
            messages.success(request, "Shipment deleted successfully.")
            return redirect("shipments")

        if action in ("create", "update"):
            shipment = (
                get_object_or_404(shipments, pk=shipment_pk)
                if action == "update"
                else shipments()
            )

            shipment_code = request.POST.get("shipment_id", "").strip()
            tracking_number = request.POST.get(
                "tracking_number", ""
            ).strip()
            carrier = request.POST.get("carrier", "").strip()
            status_value = request.POST.get("status", "Preparing")
            order_pk = request.POST.get("order")
            date_value = request.POST.get("shipment_date", "").strip()

            valid_statuses = {v for v, _ in shipments.STATUS_CHOICES}

            if not shipment_code or not tracking_number or not carrier:
                messages.error(
                    request,
                    "Shipment ID, tracking number and carrier are required.",
                )
                return redirect("shipments")

            if status_value not in valid_statuses:
                messages.error(request, "Invalid shipment status.")
                return redirect("shipments")

            duplicate = shipments.objects.filter(
                shipment_id=shipment_code
            ).exclude(pk=shipment.pk if shipment.pk else None).exists()

            if duplicate:
                messages.error(request, "Shipment ID already exists.")
                return redirect("shipments")

            try:
                order = orders.objects.get(pk=order_pk)
            except (orders.DoesNotExist, TypeError, ValueError):
                messages.error(request, "Select a valid order.")
                return redirect("shipments")

            duplicate_order = shipments.objects.filter(
                order=order
            ).exclude(pk=shipment.pk if shipment.pk else None).exists()

            if duplicate_order:
                messages.error(
                    request, "This order already has a shipment."
                )
                return redirect("shipments")

            shipment.shipment_id = shipment_code
            shipment.order = order
            shipment.tracking_number = tracking_number
            shipment.carrier = carrier
            shipment.status = status_value

            if date_value:
                parsed_date = parse_datetime(date_value)
                if parsed_date is None:
                    messages.error(request, "Invalid shipment date.")
                    return redirect("shipments")
                if timezone.is_naive(parsed_date):
                    parsed_date = timezone.make_aware(
                        parsed_date, timezone.get_current_timezone()
                    )
                shipment.shipment_date = parsed_date
            elif not shipment.pk:
                shipment.shipment_date = timezone.now()

            try:
                shipment.save()
            except IntegrityError:
                messages.error(request, "Could not save the shipment.")
                return redirect("shipments")

            messages.success(
                request,
                "Shipment created successfully."
                if action == "create"
                else "Shipment updated successfully.",
            )
            return redirect("shipments")

    queryset = shipments.objects.select_related(
        "order"
    ).order_by("-shipment_date")

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        queryset = queryset.filter(
            Q(shipment_id__icontains=search_query)
            | Q(order__order_number__icontains=search_query)
            | Q(order__customer_name__icontains=search_query)
            | Q(tracking_number__icontains=search_query)
            | Q(carrier__icontains=search_query)
        )

    valid_shipment_statuses = {v for v, _ in shipments.STATUS_CHOICES}
    if status_filter in valid_shipment_statuses:
        queryset = queryset.filter(status=status_filter)
    else:
        status_filter = ""

    edit_shipment = None
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_shipment = get_object_or_404(shipments, pk=edit_id)

    available_orders = orders.objects.exclude(
        shipment__isnull=False
    ).order_by("-order_date")

    if edit_shipment:
        available_orders = orders.objects.filter(
            Q(shipment__isnull=True) | Q(pk=edit_shipment.order_id)
        ).distinct().order_by("-order_date")

    return render(request, "shipments.html", {
        "shipments": queryset,
        "total_shipments": shipments.objects.count(),
        "preparing_shipments": shipments.objects.filter(
            status="Preparing"
        ).count(),
        "in_transit_shipments": shipments.objects.filter(
            status="In Transit"
        ).count(),
        "delivered_shipments": shipments.objects.filter(
            status="Delivered"
        ).count(),
        "available_orders": available_orders,
        "edit_shipment": edit_shipment,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": shipments.STATUS_CHOICES,
    })
    # Pagination
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    available_orders = orders.objects.exclude(
        shipment__isnull=False
    ).order_by("-order_date")

    if edit_shipment:
        available_orders = orders.objects.filter(
            Q(shipment__isnull=True) |
            Q(pk=edit_shipment.order_id)
        ).distinct().order_by("-order_date")

    context = {
        "shipments": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "total_shipments": shipments.objects.count(),
        "preparing_shipments": shipments.objects.filter(
            status="Preparing"
        ).count(),
        "in_transit_shipments": shipments.objects.filter(
            status="In Transit"
        ).count(),
        "delivered_shipments": shipments.objects.filter(
            status="Delivered"
        ).count(),
        "available_orders": available_orders,
        "edit_shipment": edit_shipment,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": shipments.STATUS_CHOICES,
    }

    return render(request, "shipments.html", context)

# =========================================================
# SHIPMENT REST API
# =========================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def shipment_api(request):
    if request.method == "GET":
        queryset = shipments.objects.select_related(
            "order"
        ).order_by("-shipment_date")

        search = request.query_params.get("q", "").strip()
        status_filter = request.query_params.get("status", "").strip()

        if search:
            queryset = queryset.filter(
                Q(shipment_id__icontains=search)
                | Q(tracking_number__icontains=search)
                | Q(carrier__icontains=search)
                | Q(order__order_number__icontains=search)
                | Q(order__customer_name__icontains=search)
            )

        if status_filter in {v for v, _ in shipments.STATUS_CHOICES}:
            queryset = queryset.filter(status=status_filter)

        return Response(ShipmentSerializer(queryset, many=True).data)

    serializer = ShipmentSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        shipment = serializer.save()
    except IntegrityError:
        return Response(
            {"detail": "Shipment ID must be unique and each order can have one shipment."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ShipmentSerializer(shipment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def shipment_detail_api(request, shipment_pk):
    shipment = get_object_or_404(
        shipments.objects.select_related("order"),
        pk=shipment_pk,
    )

    if request.method == "GET":
        return Response(ShipmentSerializer(shipment).data)

    if request.method in ("PUT", "PATCH"):
        serializer = ShipmentSerializer(
            shipment,
            data=request.data,
            partial=(request.method == "PATCH"),
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            saved_shipment = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Could not update shipment. Check its ID and order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ShipmentSerializer(saved_shipment).data)

    shipment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def analytics_view(request):
    today = timezone.localdate()
    all_products = products.objects.all()

    # --------------------------------------------------
    # 1. INVENTORY STATISTICS
    # --------------------------------------------------
    total_products = all_products.count()

    total_units = (
        all_products.aggregate(total=Sum("quantity"))["total"] or 0
    )

    stock_value_expression = ExpressionWrapper(
        F("quantity") * F("price"),
        output_field=DecimalField(
            max_digits=16,
            decimal_places=2,
        ),
    )

    inventory_value = (
        all_products.aggregate(
            total=Sum(stock_value_expression)
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------
    # 2. STOCK HEALTH
    # --------------------------------------------------
    out_of_stock = all_products.filter(
        quantity__lte=0
    ).count()

    low_stock = all_products.filter(
        quantity__gt=0,
        quantity__lte=F("reorder_level"),
    ).count()

    healthy_stock = all_products.filter(
        quantity__gt=F("reorder_level")
    ).count()

    low_stock_products = all_products.filter(
        quantity__lte=F("reorder_level")
    ).order_by("quantity", "name")

    stock_chart_labels = [
        "Healthy Stock",
        "Low Stock",
        "Out of Stock",
    ]

    stock_chart_values = [
        healthy_stock,
        low_stock,
        out_of_stock,
    ]

    # --------------------------------------------------
    # 3. EXPIRY STATISTICS
    # Assumes products has an expiry_date field.
    # --------------------------------------------------
    expired_products = all_products.filter(
        expiry_date__lt=today
    ).count()

    expiring_soon = all_products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30),
    ).count()

    # --------------------------------------------------
    # 4. PRODUCTS BY CATEGORY
    # --------------------------------------------------
    category_rows = (
        all_products.values("category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    category_labels = [
        row["category"] or "Uncategorized"
        for row in category_rows
    ]

    category_values = [
        row["total"]
        for row in category_rows
    ]

    # --------------------------------------------------
    # 5. ORDER STATUS
    # Assumes the order status field is order_status.
    # Includes every status found in the database.
    # --------------------------------------------------
    order_rows = (
        orders.objects.values("order_status")
        .annotate(total=Count("id"))
        .order_by("order_status")
    )

    order_labels = [
        row["order_status"] or "Unspecified"
        for row in order_rows
    ]

    order_values = [
        row["total"]
        for row in order_rows
    ]

    total_orders = orders.objects.count()

    # --------------------------------------------------
    # 6. SHIPMENT STATUS
    # Assumes the shipment status field is status.
    # --------------------------------------------------
    shipment_rows = (
        shipments.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    shipment_labels = [
        row["status"] or "Unspecified"
        for row in shipment_rows
    ]

    shipment_values = [
        row["total"]
        for row in shipment_rows
    ]

    # --------------------------------------------------
    # 7. STOCK MOVEMENT - LAST 7 DAYS
    # Assumes StockMovement has a created_at field.
    # --------------------------------------------------
    movement_labels = []
    movement_values = []

    for days_ago in range(6, -1, -1):
        current_day = today - timedelta(days=days_ago)

        movement_labels.append(
            current_day.strftime("%d %b")
        )

        daily_count = StockMovement.objects.filter(
            created_at__date=current_day
        ).count()

        movement_values.append(daily_count)

    # --------------------------------------------------
    # 8. TOP 5 PRODUCTS BY INVENTORY VALUE
    # --------------------------------------------------
    top_products = (
        all_products.annotate(
            stock_value=stock_value_expression
        )
        .order_by("-stock_value", "name")[:5]
    )

    top_product_labels = [
        product.name
        for product in top_products
    ]

    top_product_values = [
        float(product.stock_value or 0)
        for product in top_products
    ]

    # --------------------------------------------------
    # 9. SEND ALL DATA TO THE TEMPLATE
    # --------------------------------------------------
    context = {
        # Inventory KPIs
        "total_products": total_products,
        "total_units": total_units,
        "inventory_value": inventory_value,

        # Stock KPIs
        "healthy_stock": healthy_stock,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "low_stock_products": low_stock_products,

        # Expiry KPIs
        "expired_products": expired_products,
        "expiring_soon": expiring_soon,

        # Orders and shipments
        "total_orders": total_orders,

        # Stock health chart
        "stock_chart_labels": stock_chart_labels,
        "stock_chart_values": stock_chart_values,

        # Category chart
        "category_labels": category_labels,
        "category_values": category_values,

        # Order chart
        "order_labels": order_labels,
        "order_values": order_values,

        # Shipment chart
        "shipment_labels": shipment_labels,
        "shipment_values": shipment_values,

        # Movement chart
        "movement_labels": movement_labels,
        "movement_values": movement_values,

        # Top products chart
        "top_product_labels": top_product_labels,
        "top_product_values": top_product_values,
    }

    return render(request, "analytics.html", context)

@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not name or not email or not subject or len(message) < 10:
            messages.error(
                request,
                "Please complete all required fields and enter a "
                "message of at least 10 characters.",
            )
            return redirect("contact")

        # TODO: Save the enquiry to a database model or send it
        # to your support email before confirming receipt.

        messages.success(
            request,
            "Thank you for contacting Wareloom. Your form was validated.",
        )
        return redirect("contact")

    return render(request, "contact.html")

@login_required
def expiry_rescue(request):
    today = timezone.localdate()
    cutoff_date = today + timedelta(days=30)

    # Products that have already expired
    expired_products = products.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today,
        quantity__gt=0,
    ).order_by("expiry_date")

    # Products expiring within the next 30 days,
    # including products expiring today
    expiring_soon = products.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=cutoff_date,
        quantity__gt=0,
    ).order_by("expiry_date")

    context = {
        "expired_products": expired_products,
        "expiring_soon": expiring_soon,
        "expired_count": expired_products.count(),
        "expiring_count": expiring_soon.count(),
        "today": today,
    }

    return render(request, "expiry_rescue.html", context)


# ==========================================
# STOCKSENSE - SMART RESTOCKING
# ==========================================

@login_required
def stock_sense(request):
    all_products = products.objects.all().order_by("quantity")

    stock_items = []

    for product in all_products:
        reorder_level = product.reorder_level
        quantity = product.quantity

        if quantity <= 0:
            stock_status = "Out of Stock"
        elif quantity <= reorder_level:
            stock_status = "Low Stock"
        else:
            stock_status = "Healthy"

        # Target stock = twice the configured reorder level.
        # This is a simple rule, not a demand forecast.
        suggested_quantity = max(
            (reorder_level * 2) - quantity,
            0
        )

        stock_items.append({
            "product": product,
            "stock_status": stock_status,
            "suggested_quantity": suggested_quantity,
        })

    context = {
        "stock_items": stock_items,
        "total_products": len(stock_items),
        "low_stock_count": sum(
            1 for item in stock_items
            if item["stock_status"] == "Low Stock"
        ),
        "out_of_stock_count": sum(
            1 for item in stock_items
            if item["stock_status"] == "Out of Stock"
        ),
        "healthy_count": sum(
            1 for item in stock_items
            if item["stock_status"] == "Healthy"
        ),
    }

    return render(request, "stock_sense.html", context)




@login_required
def inventory_time_machine(request):
    movements = StockMovement.objects.select_related(
        "product", "performed_by"
    ).all()

    # Search by product name, SKU, or reason
    search = request.GET.get("q", "").strip()
    if search:
        movements = movements.filter(
            Q(product__name__icontains=search)
            | Q(product__sku__icontains=search)
            | Q(reason__icontains=search)
        )

    # Filter by movement type
    movement_type = request.GET.get("type", "").strip()
    valid_types = {
        choice[0] for choice in StockMovement.MOVEMENT_TYPES
    }

    if movement_type in valid_types:
        movements = movements.filter(movement_type=movement_type)

    context = {
        "movements": movements[:200],
        "search": search,
        "selected_type": movement_type,
        "movement_types": StockMovement.MOVEMENT_TYPES,
        "total_movements": movements.count(),
    }

    return render(
        request,
        "inventory_time_machine.html",
        context,
    )





# ==========================================================
# REPORTS & ALERTS
# ==========================================================

@login_required
def reports_alerts(request):
    today = timezone.localdate()

    # Stock alerts
    out_of_stock_products = products.objects.filter(
        quantity__lte=0
    ).order_by("name")

    low_stock_products = products.objects.filter(
        quantity__gt=0,
        quantity__lte=F("reorder_level"),
    ).order_by("quantity", "name")

    # Order alerts: orders whose expected delivery date has passed
    overdue_orders = orders.objects.filter(
        expected_delivery_date__lt=today,
    ).exclude(
        order_status__in=["Delivered", "Cancelled"]
    ).order_by("expected_delivery_date")

    # Shipment alerts
    delayed_shipments = shipments.objects.filter(
        status="Delayed"
    ).select_related("order").order_by("shipment_date")

    active_shipments = shipments.objects.filter(
        status__in=["Preparing", "Shipped", "In Transit"]
    ).count()

    pending_orders_count = orders.objects.filter(
        order_status="Pending"
    ).count()

    # Inventory valuation
    value_expression = ExpressionWrapper(
        F("quantity") * F("price"),
        output_field=DecimalField(
            max_digits=16,
            decimal_places=2,
        ),
    )

    inventory_value = (
        products.objects.aggregate(
            total=Sum(value_expression)
        )["total"] or Decimal("0.00")
    )

    # Count distinct operational alert groups.
    critical_alert_count = (
        out_of_stock_products.count()
        + delayed_shipments.count()
    )

    warning_alert_count = (
        low_stock_products.count()
        + overdue_orders.count()
    )

    context = {
        "today": today,

        "total_products": products.objects.count(),
        "total_orders": orders.objects.count(),
        "inventory_value": inventory_value,

        "out_of_stock_products": out_of_stock_products,
        "out_of_stock_count": out_of_stock_products.count(),

        "low_stock_products": low_stock_products,
        "low_stock_count": low_stock_products.count(),

        "overdue_orders": overdue_orders,
        "overdue_orders_count": overdue_orders.count(),

        "delayed_shipments": delayed_shipments,
        "delayed_shipments_count": delayed_shipments.count(),

        "pending_orders_count": pending_orders_count,
        "active_shipments_count": active_shipments,

        "critical_alert_count": critical_alert_count,
        "warning_alert_count": warning_alert_count,
    }

    return render(request, "reports_alerts.html", context)


# ==========================================================
# SHARED CSV EXPORT HELPER
# ==========================================================

@login_required
def export_report_csv(request, report_type):
    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )

    response.write("\ufeff")  # Excel-friendly UTF-8 BOM
    writer = csv.writer(response)

    if report_type == "inventory":
        response["Content-Disposition"] = (
            'attachment; filename="wareloom_inventory_report.csv"'
        )

        writer.writerow([
            "Product Name",
            "SKU",
            "Category",
            "Supplier",
            "Location",
            "Quantity",
            "Reorder Level",
            "Unit Price",
            "Inventory Value",
            "Stock Status",
        ])

        for product in products.objects.all().order_by("name"):
            quantity = product.quantity or 0
            price = product.price or Decimal("0")

            if quantity <= 0:
                status = "Out of Stock"
            elif quantity <= product.reorder_level:
                status = "Low Stock"
            else:
                status = "Healthy"

            writer.writerow([
                product.name,
                product.sku,
                product.category,
                product.supplier,
                product.location,
                quantity,
                product.reorder_level,
                price,
                quantity * price,
                status,
            ])

    elif report_type == "orders":
        response["Content-Disposition"] = (
            'attachment; filename="wareloom_orders_report.csv"'
        )

        writer.writerow([
            "Order Number",
            "Order Date",
            "Customer",
            "Product",
            "Quantity",
            "Total Amount",
            "Order Status",
            "Payment Status",
            "Expected Delivery",
        ])

        for order in orders.objects.select_related(
            "product"
        ).order_by("-order_date"):
            writer.writerow([
                order.order_number,
                order.order_date,
                order.customer_name,
                order.product.name,
                order.quantity,
                order.total_amount,
                order.order_status,
                order.payment_status,
                order.expected_delivery_date or "",
            ])

    elif report_type == "shipments":
        response["Content-Disposition"] = (
            'attachment; filename="wareloom_shipments_report.csv"'
        )

        writer.writerow([
            "Shipment ID",
            "Order Number",
            "Customer",
            "Carrier",
            "Tracking Number",
            "Shipment Date",
            "Shipment Status",
        ])

        for shipment in shipments.objects.select_related(
            "order"
        ).order_by("-shipment_date"):
            writer.writerow([
                shipment.shipment_id,
                shipment.order.order_number,
                shipment.order.customer_name,
                shipment.carrier,
                shipment.tracking_number,
                shipment.shipment_date,
                shipment.status,
            ])

    elif report_type == "valuation":
        response["Content-Disposition"] = (
            'attachment; filename="wareloom_inventory_valuation.csv"'
        )

        writer.writerow([
            "Product Name",
            "SKU",
            "Quantity",
            "Unit Price",
            "Inventory Value",
        ])

        total_value = Decimal("0")

        for product in products.objects.all().order_by("name"):
            quantity = product.quantity or 0
            price = product.price or Decimal("0")
            value = quantity * price
            total_value += value

            writer.writerow([
                product.name,
                product.sku,
                quantity,
                price,
                value,
            ])

        writer.writerow([])
        writer.writerow(["", "", "", "Total Inventory Value", total_value])

    else:
        return HttpResponse(
            "Unknown report type.",
            status=404,
        )

    return response
