from rest_framework import serializers
from .models import Profile


class ProfileCreateSerializer(serializers.Serializer):
    """
    Validates incoming POST /api/profiles request body.
    Only one field needed — name.
    """
    name = serializers.CharField(required=True, allow_blank=False)

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError('name cannot be empty')

        if any(char.isdigit() for char in value):
            raise serializers.ValidationError('name must not contain numbers')

        return value.lower()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Formats a Profile model instance into the full response dict.
    Used in POST response, GET /api/profiles/{id} response.
    """
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'gender', 'gender_probability',
            'sample_size', 'age', 'age_group',
            'country_id', 'country_name', 'country_probability',
            'created_at'
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
