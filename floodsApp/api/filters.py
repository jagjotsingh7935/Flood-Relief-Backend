import django_filters
from floodsApp.models import *

class TempPersonDataFormFilter(django_filters.FilterSet):
    farmer_name = django_filters.CharFilter(
        field_name='temp_form__farmerName',
        lookup_expr='icontains',
        label='Farmer Name'
    )
    village_name = django_filters.CharFilter(
        field_name='village__display_name',
        lookup_expr='icontains',
        label='Village Name'
    )
    mobile_number = django_filters.CharFilter(
        field_name='temp_form__mobileNumber',
        lookup_expr='icontains',
        label='Mobile Number'
    )
    is_processed = django_filters.BooleanFilter(
        field_name='is_processed',
        label='Is Processed'
    )

    class Meta:
        model = TempPersonDataForm
        fields = ['farmer_name', 'village_name', 'mobile_number', 'is_processed']