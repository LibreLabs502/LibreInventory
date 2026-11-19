from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import CompanyModel


class Warehouse(CompanyModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [models.UniqueConstraint(fields=["company", "name"], name="unique_company_warehouse_name")]

    def __str__(self):
        return self.name


class StockBalance(CompanyModel):
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_balances",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="stock_balances",
    )
    quantity_on_hand = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    quantity_reserved = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "product"],
                name="unique_warehouse_product",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_on_hand__gte=0) & models.Q(quantity_reserved__gte=0),
                name="stock_quantities_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_reserved__lte=models.F("quantity_on_hand")),
                name="stock_reserved_within_on_hand",
            ),
        ]

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def clean(self):
        super().clean()
        if self.product_id and self.product.kind != "STOCKABLE":
            raise ValidationError({"product": "Los servicios no manejan inventario."})


class StockReservation(CompanyModel):
    sale_item = models.ForeignKey(
        "sales.SaleItem",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="reservations")
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    status = models.CharField(
        max_length=10,
        choices=[("ACTIVE", "Activa"), ("CONSUMED", "Consumida"), ("RELEASED", "Liberada")],
        default="ACTIVE",
    )

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name="reservation_quantity_positive")]

    def clean(self):
        super().clean()
        if self.sale_item_id:
            if self.sale_item.product.kind != "STOCKABLE":
                raise ValidationError({"sale_item": "Los servicios no se reservan."})
            if self.warehouse_id != self.sale_item.sale.warehouse_id:
                raise ValidationError({"warehouse": "La reserva debe usar la bodega de la venta."})


class StockMovement(CompanyModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    quantity_delta = models.DecimalField(max_digits=14, decimal_places=3)
    kind = models.CharField(
        max_length=10,
        choices=[("PURCHASE", "Compra"), ("SALE", "Venta"), ("ADJUSTMENT", "Ajuste"), ("REVERSAL", "Reversión")],
    )
    purchase_item = models.ForeignKey(
        "purchases.PurchaseItem",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
    )
    sale_item = models.ForeignKey(
        "sales.SaleItem",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
    )
    reverses = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        related_name="reversal",
        null=True,
        blank=True,
    )
    reason = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity_delta=0),
                name="stock_movement_nonzero",
            ),
            models.CheckConstraint(condition=(
                models.Q(
                    kind="PURCHASE",
                    purchase_item__isnull=False,
                    sale_item__isnull=True,
                    reverses__isnull=True,
                    quantity_delta__gt=0,
                )
                | models.Q(kind="SALE", sale_item__isnull=False, purchase_item__isnull=True, reverses__isnull=True, quantity_delta__lt=0)
                | models.Q(kind="ADJUSTMENT", purchase_item__isnull=True, sale_item__isnull=True, reverses__isnull=True)
                | models.Q(kind="REVERSAL", purchase_item__isnull=True, sale_item__isnull=True, reverses__isnull=False)
            ), name="stock_movement_valid_source"),
        ]

    def clean(self):
        super().clean()
        if self.product_id and self.product.kind != "STOCKABLE":
            raise ValidationError({"product": "Los servicios no generan movimientos."})
        for field, document in [("purchase_item", "purchase"), ("sale_item", "sale")]:
            item = getattr(self, field)
            if item and (item.product_id != self.product_id or getattr(item, document).warehouse_id != self.warehouse_id):
                raise ValidationError({field: "El producto y la bodega deben coincidir con el documento."})
        if self.reverses_id:
            original = self.reverses
            if original.kind == "REVERSAL" or original.pk == self.pk or original.product_id != self.product_id or original.warehouse_id != self.warehouse_id or self.quantity_delta != -original.quantity_delta:
                raise ValidationError({"reverses": "La reversión debe invertir el movimiento original, con el mismo producto y bodega."})
