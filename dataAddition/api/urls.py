from django.urls import path
from .views import *

urlpatterns = [


    path('data/add/district/',AddNewDistrict.as_view(),name='data-add-district'),

    path('data/add/tehsil/',AddNewTehsil.as_view(),name='data-add-tehsil'),


    path('data/add/village/',AddNewVillage.as_view(),name='data-add-village'),

    path('top/card/stats/',TopCardsStats.as_view(),name='top-card-stats'),


    path('affected/villages/pdf/',AffectedVillagesPdf.as_view(),name='affected-villages-pdf'),


]