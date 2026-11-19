from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import CompanyModel


class Purchase(CompanyModel):
    supplier = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    number = models.CharField(max_length=40)
    supplier_reference = models.CharField(max_length=100, blank=True)
    purchased_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=12,
        choices=[("DRAFT", "Borrador"), ("CONFIRMED", "Confirmada"), ("CANCELLED", "Cancelada")],
        default="DRAFT",
    )
    total = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-purchased_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="unique_company_purchase_number",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="purchase_total_nonnegative",
            ),
        ]

    def __str__(self):
        return self.number


class PurchaseItem(CompanyModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit_cost = models.DecimalField(
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
                name="purchase_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0) & models.Q(line_total__gte=0),
                name="purchase_item_amounts_nonnegative",
            ),
        ]
