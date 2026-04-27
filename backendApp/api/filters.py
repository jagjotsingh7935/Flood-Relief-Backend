import django_filters
from django.db.models import Q
from backendApp.models import *




class AdminFilter(django_filters.FilterSet):
    is_active = django_filters.CharFilter(lookup_expr='iexact')
    
    class Meta:
        model = AdminFitness
        fields = ['is_active']

