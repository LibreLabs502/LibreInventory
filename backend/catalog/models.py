from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from common.models import CompanyModel


class Product(CompanyModel):
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(
        max_length=12,
        choices=[("STOCKABLE", "Producto"), ("SERVICE", "Servicio")],
        default="STOCKABLE",
    )
    unit = models.CharField(
        max_length=10,
        choices=[("UNIT", "Unidad"), ("KG", "Kilogramo"), ("LITER", "Litro"), ("METER", "Metro"), ("HOUR", "Hora")],
        default="UNIT",
    )
    sale_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    minimum_stock = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "sku"], name="unique_company_sku"),
            models.CheckConstraint(
                condition=models.Q(sale_price__gte=0),
                name="product_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_stock__gte=0),
                name="product_minimum_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
