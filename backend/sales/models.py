from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import CompanyModel


class Sale(CompanyModel):
    customer = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.PROTECT,
        related_name="sales",
        null=True,
        blank=True,
    )
    quotation = models.ForeignKey(
        "quotations.Quotation",
        on_delete=models.PROTECT,
        related_name="sales",
        null=True,
        blank=True,
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="sales",
    )
    number = models.CharField(max_length=40)
    kind = models.CharField(
        max_length=10,
        choices=[("IMMEDIATE", "Inmediata"), ("ORDER", "Pedido")],
        default="IMMEDIATE",
    )
    status = models.CharField(
        max_length=12,
        choices=[("DRAFT", "Borrador"), ("CONFIRMED", "Confirmada"), ("FULFILLED", "Entregada"), ("CANCELLED", "Cancelada")],
        default="DRAFT",
    )
    sold_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    delivery_address = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    total = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-sold_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="unique_company_sale_number",
            ),
            models.CheckConstraint(condition=models.Q(total__gte=0), name="sale_total_nonnegative"),
        ]

    def __str__(self):
        return self.number


class SaleItem(CompanyModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )
    # Copias históricas: cambiar el catálogo no modifica los documentos anteriores.
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    line_total = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="sale_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0) & models.Q(line_total__gte=0),
                name="sale_item_amounts_nonnegative",
            ),
        ]
