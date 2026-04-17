from django.db import models
import uuid6


class Profile(models.Model):

    class AgeGroup(models.TextChoices):
        CHILD = 'child', 'Child'
        TEENAGER = 'teenager', 'Teenager'
        ADULT = 'adult', 'Adult'
        SENIOR = 'senior', 'Senior'

    id = models.UUIDField(primary_key=True, default=uuid6.uuid7)
    name = models.CharField(max_length=255, unique=True)

    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField()
    sample_size = models.IntegerField()

    age = models.IntegerField()
    age_group = models.CharField(max_length=10, choices=AgeGroup.choices)

    country_id = models.CharField(max_length=5)
    country_probability = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name