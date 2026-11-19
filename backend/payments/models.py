from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import CompanyModel


class Payment(CompanyModel):
    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    purchase = models.ForeignKey(
        "purchases.Purchase",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    direction = models.CharField(max_length=3, choices=[("IN", "Entrada"), ("OUT", "Salida")])
    kind = models.CharField(
        max_length=7,
        choices=[("PAYMENT", "Pago"), ("REFUND", "Reembolso")],
        default="PAYMENT",
    )
    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    method = models.CharField(
        max_length=10,
        choices=[("CASH", "Efectivo"), ("TRANSFER", "Transferencia"), ("CARD", "Tarjeta"), ("OTHER", "Otro")],
    )
    reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=6,
        choices=[("POSTED", "Registrado"), ("VOIDED", "Anulado")],
        default="POSTED",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-paid_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=(models.Q(sale__isnull=False, purchase__isnull=True) | models.Q(sale__isnull=True, purchase__isnull=False)),
                name="payment_exactly_one_document",
            ),
            models.CheckConstraint(condition=(
                models.Q(sale__isnull=False, kind="PAYMENT", direction="IN")
                | models.Q(sale__isnull=False, kind="REFUND", direction="OUT")
                | models.Q(purchase__isnull=False, kind="PAYMENT", direction="OUT")
                | models.Q(purchase__isnull=False, kind="REFUND", direction="IN")
            ), name="payment_valid_direction"),
        ]
