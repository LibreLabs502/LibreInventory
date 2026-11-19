from django.db import models


class CompanyModel(models.Model):
    """Campos compartidos; este modelo abstracto no crea una tabla."""

    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        # Evita relacionar registros de empresas distintas al ejecutar full_clean().
        # save() no llama full_clean(): los futuros serializers también deben validar.
        super().clean()
        from django.core.exceptions import ValidationError

        errors = {}
        for field in self._meta.fields:
            if not isinstance(field, models.ForeignKey) or field.name == "company":
                continue
            if not getattr(self, field.attname):
                continue
            related = getattr(self, field.name)
            if hasattr(related, "company_id") and related.company_id != self.company_id:
                errors[field.name] = "El registro debe pertenecer a la misma empresa."
        if errors:
            raise ValidationError(errors)
