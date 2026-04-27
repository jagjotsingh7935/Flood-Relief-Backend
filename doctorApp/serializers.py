
from rest_framework import serializers
from .models import *
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

import base64
import re
import uuid
from django.core.files.base import ContentFile
from django.conf import settings

#---------------------------------------------------------------Doctor-------------------------------------------------------------------



class DoctorTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorTimeSlot
        fields = ['id', 'startTime', 'endTime', 'isOnline', 'isOffline']


class DoctorScheduleTemplateSerializer(serializers.ModelSerializer):
    time_slots = DoctorTimeSlotSerializer(many=True)

    class Meta:
        model = DoctorScheduleTemplate
        fields = ['id', 'day_of_week', 'is_active', 'time_slots']

    def create(self, validated_data):
        time_slots_data = validated_data.pop('time_slots')
        schedule, created = DoctorScheduleTemplate.objects.get_or_create(
            day_of_week=validated_data['day_of_week'],
            defaults=validated_data
        )
        if not created:
            schedule.time_slots.all().delete()
        for time_slot_data in time_slots_data:
            DoctorTimeSlot.objects.create(schedule=schedule, **time_slot_data)
        return schedule

    def update(self, instance, validated_data):
        time_slots_data = validated_data.pop('time_slots')
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        instance.time_slots.all().delete()
        for time_slot_data in time_slots_data:
            DoctorTimeSlot.objects.create(schedule=instance, **time_slot_data)
        return instance
    
####   
class DoctorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorLogModel
        fields = '__all__'
####

class DoctorExceptionTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorExceptionTimeSlot
        fields = ['id', 'startTime', 'endTime', 'isOnline', 'isOffline']

class DoctorScheduleExceptionSerializer(serializers.ModelSerializer):
    time_slots = DoctorExceptionTimeSlotSerializer(many=True, required=False)

    class Meta:
        model = DoctorScheduleException
        fields = ['id', 'date', 'is_holiday', 'time_slots']

    def create(self, validated_data):
        time_slots_data = validated_data.pop('time_slots', [])
        exception = DoctorScheduleException.objects.create(**validated_data)
        for time_slot_data in time_slots_data:
            DoctorExceptionTimeSlot.objects.create(exception_day=exception, **time_slot_data)
        return exception
    

####
class DoctorExceptionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorExceptionLogModel
        fields = '__all__'

####
#-----------------------------------------------------------------user-----------------------------------------------------------

class UserSlotSerializer(serializers.ModelSerializer):
    # payment_screenshot = serializers.SerializerMethodField()

    

    class Meta:
        model = UserSlot
        fields = '__all__'


    # def get_payment_screenshot(self, obj):
    #     try:
    #         screenshot = PaymentScreenshot.objects.get(user_slot=obj)
    #         request = self.context.get('request')
    #         image_url = (
    #             request.build_absolute_uri(screenshot.image.url)
    #             if request
    #             else screenshot.image.url
    #         )

    #         return {
    #             'id': screenshot.id,
    #             'image_url': image_url,
    #             'first_name': screenshot.first_name,
    #             'last_name': screenshot.last_name,
    #             'email': screenshot.email,
    #             'phone_number': screenshot.phone_number,
    #             'uploaded_at': screenshot.uploaded_at
    #         }
    #     except PaymentScreenshot.DoesNotExist:
    #         return None


    def validate(self, data):
        date = data.get('date')
        startTime = data.get('startTime')
        endTime = data.get('endTime')
        isOnline = data.get('isOnline')
        isOffline = data.get('isOffline')
        


        print("date",date,startTime,endTime,isOnline,isOffline)


        #check the instance

        instance = self.instance


        # Check if both isOnline and isOffline are not selected
        if not isOffline and not isOnline:
            raise serializers.ValidationError("Please select a mode (Online or Offline) for the appointment.")

        # Validate time range
        if startTime and endTime and startTime >= endTime:
            raise serializers.ValidationError("End time must be after start time.")

        # Check if the time slot is already booked for the specific date
        existing_bookings = UserSlot.objects.filter(
            date=date,
            startTime__lt=endTime,
            endTime__gt=startTime,
           
        )

        if instance:
            existing_bookings = existing_bookings.exclude(id=instance.id)

        # For online bookings, only check conflicts with other online bookings
        if isOnline:
            online_conflicts = existing_bookings.filter(isOnline=True,payment_status__in=["success", "on hold"])
            if online_conflicts.exists():
                raise serializers.ValidationError(
                    "This time slot is already booked for an online meeting."
                )

        # For offline bookings, only check conflicts with other offline bookings
        if isOffline:
            offline_conflicts = existing_bookings.filter(isOffline=True,payment_status__in=["success", "on hold"])
            if offline_conflicts.exists():
                raise serializers.ValidationError(
                    "This time slot is already booked for an offline meeting."
                )

        return data
    


class UserSlotLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSlotLogModel
        fields = '__all__'


class FeesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeesModel
        fields = '__all__'
#---------------------------------------------------------------Razory pay Details----------------------------------------------------------------



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['razorpay_payment_id', 'razorpay_signature', 'status']



