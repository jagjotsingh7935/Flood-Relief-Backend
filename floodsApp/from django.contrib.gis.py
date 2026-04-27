from django.contrib.gis.db import models as gis_models
from django.db import models
from accounts.models import User

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Location Hierarchy (One-to-Many relationships)
class State(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=3, blank=True)  # e.g., "PB" for Punjab
    
    class Meta:
        verbose_name_plural = "States"
    
    def __str__(self):
        return self.name

class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['state', 'name']
        verbose_name_plural = "Cities"
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"

class Tehsil(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='tehsils')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['city', 'name']
        verbose_name_plural = "Tehsils"
    
    def __str__(self):
        return f"{self.name}, {self.city.name}"

class Village(TimeStampModel):
    tehsil = models.ForeignKey(Tehsil, on_delete=models.CASCADE, related_name='villages')
    display_name = models.CharField(max_length=150)
    # Use proper decimal fields for coordinates
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    pin_code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['tehsil', 'display_name', 'pin_code']
        verbose_name_plural = "Villages"
    
    def __str__(self):
        return self.display_name

# Verification Model
class VerifiedBy(TimeStampModel):
    verification_image = models.ImageField(
        upload_to='verification_images/%Y/%m/%d/',
        help_text="Image verifying the farmer's information"
    )
    surveyor_name = models.CharField(max_length=100)
    surveyor_mobile = models.CharField(max_length=15, blank=True)
    date = models.DateField()
    is_verified = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['surveyor_name', 'date']  # One verification per surveyor per day
    
    def __str__(self):
        return f"Verification by {self.surveyor_name} on {self.date}"

# Farmer Form with proper field types
class FarmerForm(TimeStampModel):
    # Relations
    verified_by = models.ForeignKey(
        VerifiedBy, 
        on_delete=models.CASCADE, 
        related_name='verified_forms'
    )
    farmer_image = models.ImageField(
        upload_to='farmer_images/%Y/%m/%d/',
        help_text="Photo of the farmer"
    )
    
    # Personal Information
    farmer_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=254, blank=True)
    
    # Location (via TempPersonDataForm)
    # House Status
    HOUSE_STATUS_CHOICES = [
        ('undamaged', 'Undamaged'),
        ('partially_damaged', 'Partially Damaged'),
        ('fully_damaged', 'Fully Damaged'),
        ('uninhabitable', 'Uninhabitable'),
    ]
    house_status = models.CharField(max_length=20, choices=HOUSE_STATUS_CHOICES)
    
    # Land Information
    total_land_owned = models.DecimalField(max_digits=8, decimal_places=2, help_text="In acres")
    land_affected = models.DecimalField(max_digits=8, decimal_places=2, help_text="In acres")
    
    # Crop Information
    crops_planted = models.CharField(max_length=200, help_text="List of crops")
    crops_lost = models.CharField(max_length=200, blank=True)
    estimated_crop_loss = models.CharField(max_length=100, help_text="Amount range")
    
    # Requirements (Boolean fields would be better)
    tractor_leveling = models.CharField(max_length=100, blank=True)
    manure_fertilizer = models.CharField(max_length=100, blank=True)
    seeds_required = models.CharField(max_length=100, blank=True)
    fertilizers_pesticides = models.CharField(max_length=100, blank=True)
    labor_requirement = models.CharField(max_length=100, blank=True)
    irrigation_repair = models.CharField(max_length=100, blank=True)
    
    # Damage Assessment
    livestock_damage = models.CharField(max_length=100, blank=True)
    household_needs = models.CharField(max_length=200, blank=True)
    housing_repair = models.CharField(max_length=100, blank=True)
    other_support = models.CharField(max_length=200, blank=True)
    
    # Additional
    additional_notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['mobile_number', 'verified_by']
        verbose_name_plural = "Farmer Forms"
        indexes = [
            models.Index(fields=['mobile_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.farmer_name} - {self.mobile_number}"

# Junction table for linking forms to villages
class TempPersonDataForm(TimeStampModel):
    village = models.ForeignKey(
        Village, 
        on_delete=models.CASCADE, 
        related_name='temp_person_data'
    )
    temp_form = models.ForeignKey(
        FarmerForm, 
        on_delete=models.CASCADE, 
        related_name='temp_person_data_forms'
    )
    is_processed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['village', 'temp_form']
        verbose_name_plural = "Temporary Person Data Forms"
    
    def __str__(self):
        return f"Temp data for {self.temp_form.farmer_name} in {self.village.display_name}"

# Person Data (for future user integration)
class PersonData(TimeStampModel):
    village = models.ForeignKey(
        Village, 
        on_delete=models.CASCADE, 
        related_name='person_data'
    )
    form = models.OneToOneField(
        FarmerForm, 
        on_delete=models.CASCADE, 
        related_name='person_data'
    )
    user = models.OneToOneField(
        User, 
        related_name='person_data', 
        on_delete=models.CASCADE,
        blank=True, 
        null=True
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Person Data"
    
    def __str__(self):
        return f"Person data for {self.form.farmer_name}"