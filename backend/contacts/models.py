from django.db import models

from common.models import CompanyModel


class Contact(CompanyModel):
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_customer = models.BooleanField(default=True)
    is_supplier = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [models.CheckConstraint(condition=models.Q(is_customer=True) | models.Q(is_supplier=True), name="contact_has_role")]

    def __str__(self):
        return self.name
