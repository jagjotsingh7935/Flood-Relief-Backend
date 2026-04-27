from django.contrib import admin
from floodsApp.models import *
# Register your models here.


admin.site.register(State)
admin.site.register(City)
admin.site.register(Tehsil)
admin.site.register(Village)
admin.site.register(AffectedVillageMapData)
admin.site.register(VerifiedBy)
admin.site.register(FarmerForm)
admin.site.register(TempPersonDataForm)
admin.site.register(PersonData)


