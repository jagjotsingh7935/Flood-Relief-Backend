from django.db import models
from accounts.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# Create your models here.

#---------------------------------------------------------------Doctor-------------------------------------------------------------------
class DoctorScheduleTemplate(models.Model):
    """Base template for doctor's recurring schedule"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ]
    
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week']

####
class DoctorLogModel(models.Model):
    doctor = models.ForeignKey(DoctorScheduleTemplate,on_delete=models.SET_NULL,related_name='Time_SLots',null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='Time_slots')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100)
    description  = models.TextField()
    class Meta:
        ordering = ['-timestamp']
####



class DoctorTimeSlot(models.Model):
    """Individual time slots within a schedule"""
    schedule = models.ForeignKey(DoctorScheduleTemplate, related_name='time_slots', on_delete=models.CASCADE)
    startTime = models.TimeField()
    endTime = models.TimeField()
    isOnline = models.BooleanField(default=True)
    isOffline = models.BooleanField(default=True)

    def clean(self):
        if self.startTime >= self.endTime:
            raise ValidationError("End time must be after start time")

    class Meta:
        ordering = ['startTime']

class DoctorScheduleException(models.Model):
    """Exceptions to the regular schedule (holidays, modified hours, etc.)"""
    date = models.DateField()
    is_holiday = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


####
class DoctorExceptionLogModel(models.Model):
    doctor = models.ForeignKey(DoctorScheduleException,on_delete=models.SET_NULL,related_name='Exception_Time_SLots',null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='Exception_Time_slots')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100)
    description  = models.TextField()
    class Meta:
        ordering = ['-timestamp']
####



class DoctorExceptionTimeSlot(models.Model):
    """Time slots for exception days"""
    exception_day = models.ForeignKey(DoctorScheduleException, related_name='time_slots', on_delete=models.CASCADE)
    startTime = models.TimeField(null=True, blank=True)
    endTime = models.TimeField(null=True, blank=True)
    isOnline = models.BooleanField(default=True)
    isOffline = models.BooleanField(default=True)

    def clean(self):
        if self.startTime and self.endTime and self.startTime >= self.endTime:
            raise ValidationError("End time must be after start time")

#-----------------------------------------------------------------user-----------------------------------------------------------

class UserSlot(models.Model):
    firstName = models.CharField(max_length=100, null=True, blank=True)
    lastName = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    isOnline = models.BooleanField(default=False)
    isOffline = models.BooleanField(default=False)
    date = models.DateField(null=True,blank=True)
    startTime = models.TimeField(null=True, blank=True)
    endTime = models.TimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    meet_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    

    class Meta:
        ordering = ['-created_at']



class UserSlotLogModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_slot_log',null=True,blank=True)
    userSlot = models.ForeignKey(UserSlot, on_delete=models.SET_NULL, related_name='user_slot_log', null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ['-timestamp']



class ProgramImage(models.Model):
    image = models.ImageField(upload_to='books/covers/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id}"

class Program(models.Model):
    title = models.CharField(max_length=100,null=True,blank=True)
    images = models.ManyToManyField(ProgramImage, blank=True, related_name='books')
    discount = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(null=True,blank=True)



class ProductImage(models.Model):
    image = models.ImageField(upload_to='product/images/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id}"


class Product(models.Model):
    title = models.CharField(max_length=100)
    images = models.ManyToManyField(ProductImage,related_name='product',blank=True,null=True)
    cover_image = models.ImageField(upload_to='product/cover/')
    alt_text = models.TextField()
    pdf = models.FileField(upload_to='product/pdf/',null=True,blank=True)
    



class FeesModel(models.Model):
    amountOnline = models.IntegerField(null=True,blank=True)
    amountOffline = models.IntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    program = models.ForeignKey(Program,on_delete=models.CASCADE,related_name='program',null=True,blank=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:
        ordering = ['-created_at']





class ProductBuyHistory(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField(null=True,blank=True)
    is_sold = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=100,null=True,blank=True)

    product = models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




#---------------------------------------------------------------Razory pay Details----------------------------------------------------------------


class Payment(models.Model):
    user_slot = models.OneToOneField(UserSlot, on_delete=models.CASCADE, related_name='payment',null=True,blank=True)
    product_history = models.ForeignKey(ProductBuyHistory,on_delete=models.CASCADE,null=True,blank=True,related_name='paymnet_product')
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, success, failed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']







class GoogleToken(models.Model):
    token = models.TextField()
    refresh_token = models.TextField(null=True)
    token_uri = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    scopes = models.JSONField()
    expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'google_token'



