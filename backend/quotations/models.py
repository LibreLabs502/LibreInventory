from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import CompanyModel


class Quotation(CompanyModel):
    customer = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.PROTECT,
        related_name="quotations",
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=10,
        choices=[("DRAFT", "Borrador"), ("SENT", "Enviada"), ("ACCEPTED", "Aceptada"), ("REJECTED", "Rechazada"), ("EXPIRED", "Vencida")],
        default="DRAFT",
    )
    issued_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
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
        related_name="quotations",
    )

    class Meta:
        ordering = ["-issued_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="unique_company_quotation_number",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="quotation_total_nonnegative",
            ),
        ]

    def __str__(self):
        return self.number


class QuotationItem(CompanyModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="quotation_items",
    )
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
                name="quotation_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0) & models.Q(line_total__gte=0),
                name="quotation_item_amounts_nonnegative",
            ),
        ]
