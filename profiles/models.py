from django.db import models
import uuid6


class Profile(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    name = models.CharField(max_length=255, unique=True)

    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField()
    sample_size = models.IntegerField()

    age = models.IntegerField()
    age_group = models.CharField(max_length=20)

    country_id = models.CharField(max_length=5)
    country_name = models.CharField(max_length=100, default='')
    country_probability = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return self.name