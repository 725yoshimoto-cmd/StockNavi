from django.db import models

class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name
