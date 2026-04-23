import django_filters
from .models import Profile


class ProfileFilter(django_filters.FilterSet):
    """
    Declarative filter class for Profile model.
    DjangoFilterBackend reads this automatically when attached to a view.

    Exact filters (gender, country_id, age_group) use case-insensitive matching.
    Range filters (min_age, max_age) use custom methods.
    Threshold filters (min_gender_probability, min_country_probability) use gte lookup.
    """

    gender = django_filters.CharFilter(
        field_name='gender',
        lookup_expr='iexact'
    )
    country_id = django_filters.CharFilter(
        field_name='country_id',
        lookup_expr='iexact'
    )
    age_group = django_filters.CharFilter(
        field_name='age_group',
        lookup_expr='iexact'
    )

    min_age = django_filters.NumberFilter(
        field_name='age',
        lookup_expr='gte'
    )
    max_age = django_filters.NumberFilter(
        field_name='age',
        lookup_expr='lte'
    )

    min_gender_probability = django_filters.NumberFilter(
        field_name='gender_probability',
        lookup_expr='gte'
    )
    min_country_probability = django_filters.NumberFilter(
        field_name='country_probability',
        lookup_expr='gte'
    )

    class Meta:
        model = Profile
        fields = [
            'gender', 'country_id', 'age_group',
            'min_age', 'max_age',
            'min_gender_probability', 'min_country_probability'
        ]