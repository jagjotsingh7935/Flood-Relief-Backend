
import django_filters
from django.db.models import Q
from accounts.models import *


class AdminFilter(django_filters.FilterSet):
    is_active = django_filters.CharFilter(lookup_expr='iexact')
    city = django_filters.BaseInFilter(field_name='city', lookup_expr='in')  # Filter by multiple cities
    state = django_filters.BaseInFilter(field_name='state', lookup_expr='in')  # Filter by multiple states
    gender = django_filters.BaseInFilter(field_name='gender', lookup_expr='in')  # Filter by multiple genders

    class Meta:
        model = Admin
        fields = ['is_active', 'city', 'state', 'gender']

