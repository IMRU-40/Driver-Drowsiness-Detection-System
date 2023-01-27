from django.db import models

# Create your models here.
class drowsiness_history(models.Model):
    USERNAME=models.CharField(max_length=25)
    NAME=models.CharField(max_length=25)
    EMAIL=models.EmailField()
    TIME=models.DateTimeField(null=True,unique=False)