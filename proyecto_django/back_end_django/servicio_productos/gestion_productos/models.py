from django.db import models
import uuid


class Productos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.BooleanField(default=False)
    description = models.TextField()
    product_key = models.CharField(max_length=8, null=False)
    image_link = models.CharField(max_length=200, null=False)

    def __str__(self):
        return self.name
