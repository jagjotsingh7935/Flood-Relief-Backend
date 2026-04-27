from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(FeesModel)
admin.site.register(UserSlot)
admin.site.register(UserSlotLogModel)


admin.site.register(DoctorExceptionTimeSlot)
admin.site.register(DoctorScheduleException)
admin.site.register(DoctorLogModel)
admin.site.register(DoctorScheduleTemplate)
admin.site.register(DoctorExceptionLogModel)
admin.site.register(DoctorTimeSlot)
admin.site.register(GoogleToken)
