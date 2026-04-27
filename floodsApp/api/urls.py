from django.urls import path
from .views import *

urlpatterns = [


# User /Farmer

    path('farmer/data/add/user/',AddFarmerDataAPIViewUser.as_view(),name='farmer-data-add-user'),

# Admin

    path('farmer/data/add/admin/',AddFarmerDataAPIViewAdmin.as_view(),name='farmer-data-add-admin'),

    # path('temp/to/permanent/show/',ProcessTempPersonDataAPIView.as_view(),name='temp-to-permanent-show'),

    path('temp/to/permanent/create/',ProcessTempPersonDataAPIView.as_view(),name='temp-to-permanent-create'),

    path('temp/person/list/',TempPersonList.as_view(),name='temp-person-list'),


    path('temp/person/data/all/',ShowPersonTemporaryAll.as_view(),name='temp-person-data-all'),


    path('temp/person/data/by/id/',ShowPersonTemporaryById.as_view(),name='temp-person-data-by-id'),


    path('person/data/all/',ShowPersonAll.as_view(),name='person-data-by-id'),

    path('person/data/by/id/',ShowPersonById.as_view(),name='person-data-by-id'),

    path('unique/pin/code/',UniquePinCodesView.as_view(),name='unique-pin-code'),


    path('person/data/by/pin/code/', PersonDataByPinCodeView.as_view(), name='person-data-by-pin-code'),


    path('village/display/names/', VillageDisplayNamesByPinCodeView.as_view(), name='village-display-names'),


    path('add/affected/village/', AddAffectedVillageMapData.as_view(), name='add-affected-village'),

    path('affected/village/map/data/', AffectedVillageMapDataView.as_view(), name='affected-village-map-data'),

    path('affected/village/map/data/admin/', AffectedVillageMapDataViewAdmin.as_view(), name='affected-village-map-data'),


    path('update/affected/village/population/', UpdateAffectedVillagePopulation.as_view(), name='update-affected-village-population'),

    

    path('show/person/on/user/page/', ShowPersonOnUserPage.as_view(), name='show-person-on-user-page'),

    path('show/person/on/user/page/with/filters/', ShowPersonOnUserPageWithFilters.as_view(), name='show-person-on-user-page-with-filters'),


    path('download/excel/', ExportToExcelAPIView.as_view(), name='download-excel'),

    path('bulk/upload/excel/admin/', BulkUploadExcelAPIViewAdmin.as_view(), name='bulk-upload-excel-admin'),

    path('show/person/stats/', ShowPersonStats.as_view(), name='show-person-stats'),


    path('processed/unprocessed/count/', ProcessedUnprocessedCount.as_view(), name='processed-unprocessed-count'),



    path('show/farmer/amount/', ShowFarmerAmount.as_view(), name='show-farmer-amount'),

    path('add/farmer/amount/', AddFarmerAmount.as_view(), name='add-farmer-amount'),

    path('generate/person/data/pdf/', GeneratePersonDataPDF.as_view(), name='generate-person-data-pdf'),


    path('district/list/', DistrictList.as_view(), name='district-list'),

    path('tehsil/list/', TehsilList.as_view(), name='tehsil-list'),


    path('village/list/', VillageList.as_view(), name='village-list'),

    path('state/list/', StateList.as_view(), name='state-list'),


    path('village/list/for/add/data/', VillageListForAddData.as_view(), name='village-list-add-data'),


    path('show/person/on/user/page/with/filters/uisng/village/id/', ShowPersonOnUserPageWithFiltersUsingVillage.as_view(), name='show-person-on-user-page-with-filters-using-village'),




    path('export/location/data/excel/', ExportLocationDataToExcelAPIView.as_view(), name='export-location-data-excel'),



    path('generate/excel/dummy/data/', GenerateDummyDataExcelAPIView.as_view(), name='generate-excel-dummy-data'),




    path('farmer/data/admin/edit/',EditFarmerDataAPIViewAdmin.as_view(),name='farmer-data-edit-admin'),


    path('farmer/delete/', DeleteFarmerDataAPIViewAdmin.as_view(), name='farmer-delete'),

    path('farmer/get/', GetFarmerDataAPIViewAdmin.as_view(), name='farmer-get'),


]