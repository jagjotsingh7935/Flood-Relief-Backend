from django.db import models
from accounts.models import *

# Create your models here.


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    
class State(models.Model):
    name = models.CharField(max_length=50,default='Punjab')

    class Meta:
        verbose_name_plural = "States"
    
    def __str__(self):
        return self.name
    


class City(TimeStampModel):
    state = models.ForeignKey(State,related_name='state_city',on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)


    class Meta:
        # unique_together = ['state', 'name']
        verbose_name_plural = "Cities"
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Tehsil(TimeStampModel):
    city = models.ForeignKey(City,related_name='city_tehsil',on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)


    class Meta:
        # unique_together = ['city', 'name']
        verbose_name_plural = "Tehsils"
    
    def __str__(self):
        return f"{self.name}, {self.city.name}"

    

class Village(TimeStampModel):
    tehsil = models.ForeignKey(Tehsil,related_name='tehsil_village',on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100,blank=True, null=True)
    latitude = models.CharField(max_length=100,blank=True, null=True)
    pin_code = models.CharField(max_length=100,null=True,blank=True)
    is_active = models.BooleanField(default=True)


    class Meta:
        # unique_together = ['tehsil', 'display_name', 'pin_code']
        verbose_name_plural = "Villages"


class AffectedVillageMapData(models.Model):
    pin_code = models.CharField(max_length=100)
    popup = models.CharField(max_length=100,help_text='village_display_name')
    center = models.JSONField()
    zoom = models.CharField(default='14',max_length=100)
    marker = models.JSONField()
    radius = models.CharField(default='600',max_length=100)
    severity = models.CharField(max_length=100)
    population = models.CharField(max_length=100)
    village = models.ForeignKey(Village,on_delete=models.CASCADE,related_name='village_affected_data',null=True,blank=True)





class VerifiedBy(TimeStampModel):
    verification_image = models.ImageField(upload_to='media/verificationimage/',null=True,blank=True)
    surveyor_name = models.CharField(max_length=100)
    surveyor_mobile = models.CharField(max_length=15, blank=True)
    date = models.DateField()
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification by {self.surveyor_name} on {self.date}"

class FarmerForm(TimeStampModel):
    verified_by = models.ForeignKey(VerifiedBy,on_delete=models.CASCADE,related_name='verified_by')
    farmer_image = models.ImageField(upload_to='media/farmerimage/',null=True,blank=True)
    farmerName = models.CharField(max_length=100,blank=True,null=True)
    fatherName = models.CharField(max_length=100,blank=True,null=True)
    mobileNumber = models.CharField(max_length=100,blank=True,null=True)
    email = models.EmailField(max_length=100,blank=True,null=True)
    houseStatus = models.CharField(max_length=100,blank=True,null=True)
    totalLandOwned = models.CharField(max_length=100,blank=True,null=True)
    landAffected = models.CharField(max_length=100,blank=True,null=True)
    cropsPlanted = models.CharField(max_length=100,blank=True,null=True)
    cropsLost = models.CharField(max_length=100,blank=True,null=True)
    estimatedCropLoss = models.CharField(max_length=100,blank=True,null=True)
    tractorLeveling = models.CharField(max_length=100,blank=True,null=True)
    manureFertilizer = models.CharField(max_length=100,blank=True,null=True)
    seedsRequired = models.CharField(max_length=100,blank=True,null=True)
    fertilizersPesticides = models.CharField(max_length=100,blank=True,null=True)
    laborRequirement = models.CharField(max_length=100,blank=True,null=True)
    irrigationRepair = models.CharField(max_length=100,blank=True,null=True)
    livestockDamage = models.CharField(max_length=100,blank=True,null=True)
    householdNeeds = models.CharField(max_length=100,blank=True,null=True)
    housingRepair = models.CharField(max_length=100,blank=True,null=True)
    otherSupport = models.CharField(max_length=100,blank=True,null=True)
    additionalNotes = models.TextField(max_length=100,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    amount_needed = models.CharField(max_length=100,blank=True,null=True)
    amount_received = models.CharField(max_length=100,blank=True,null=True)


class TempPersonDataForm(TimeStampModel):
    village = models.ForeignKey(Village,related_name='temp_person_village',on_delete=models.CASCADE)
    temp_form = models.ForeignKey(FarmerForm,on_delete=models.CASCADE,related_name='temp_person_data_form')
    is_processed = models.BooleanField(default=False)
    # is_declined = models.BooleanField(default=False)   #new Field

    class Meta:
        # unique_together = ['village', 'temp_form']
        verbose_name_plural = "Temporary Person Data Forms"

    def __str__(self):
        return f"Temp data for {self.temp_form.farmerName} in {self.village.display_name}"

class PersonData(TimeStampModel):
    temp_person_data_form = models.ForeignKey(TempPersonDataForm,related_name ='temp_person',on_delete=models.CASCADE,null=True,blank=True)
    village = models.ForeignKey(Village,related_name='person_village',on_delete=models.CASCADE)
    form = models.ForeignKey(FarmerForm,on_delete=models.CASCADE,related_name='person_data_form')
    user=models.OneToOneField(User, related_name="person", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_single_user = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Person Data"
    
    def __str__(self):
        return f"Person data for {self.form.farmerName}"
