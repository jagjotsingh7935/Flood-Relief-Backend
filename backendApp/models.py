from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from accounts.models import User

# Create your models here.






class AdminFitness(models.Model):
    user=models.OneToOneField(User, related_name="admin_fitness", on_delete=models.CASCADE)
    username = None
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    full_name = models.CharField(max_length=200)
    avatar_image = models.ImageField(upload_to='files/accounts/admin_users_images', null=True, blank=True)
    phone_number = models.CharField(max_length=15,null=True, blank=True)
    created_at = models.DateTimeField( auto_now_add=True)
    last_updated = models.DateTimeField( auto_now=True)

    def __str__(self):
        return self.email
    


class UserLogFitness(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    )

    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user_logs_fitness', null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - {self.action} - {self.created_at}"

    class Meta:
        verbose_name = "User Log"
        verbose_name_plural = "User Logs"




# -------------------------------------------------
#  Brand model
# -------------------------------------------------
class Brand(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)              
    logo = models.ImageField(
        upload_to='brands/logos/',                    
        null=True,
        blank=True,
    )
    description = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ['name']

    def __str__(self):
        return self.name
    

# -------------------------------------------------
#  Review model
# -------------------------------------------------
class Review(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=100)
    avatar = models.ImageField(
        upload_to='reviews/avatars/',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author}"



# -------------------------------------------------
#  Certification model
# -------------------------------------------------
class Certification(models.Model):
    name = models.CharField(max_length=200, unique=True)
    image = models.ImageField(
        upload_to='certifications/images/',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
        ordering = ['name']

    def __str__(self):
        return self.name
    



# -------------------------------------------------
#  BlogPost model
# -------------------------------------------------
class BlogPost(models.Model):
    title = models.CharField(max_length=300)
    excerpt = models.TextField()
    content = models.TextField()
    image = models.ImageField(
        upload_to='blog/images/',
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=100)
    date = models.DateField()
    read_time = models.CharField(max_length=20)  
    author = models.CharField(max_length=150)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return self.title
    


# -------------------------------------------------
#  Book model
# -------------------------------------------------
class BookImage(models.Model):
    image = models.ImageField(upload_to='books/covers/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id}"

class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=150)
    
    # Primary image (optional)
    image = models.ForeignKey(
        BookImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_for_books'
    )
    
    # All images (including primary and extras)
    images = models.ManyToManyField(BookImage, blank=True, related_name='books')

    discount = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    bg_gradient = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author}"

# -------------------------------------------------
#  Testimonial model
# -------------------------------------------------
class Testimonial(models.Model):
    name = models.CharField(max_length=150)
    position = models.CharField(max_length=150)
    quote = models.TextField()
    image = models.ImageField(
        upload_to='testimonials/images/',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=150,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.position}"
    

class ContactForm(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    project = models.TextField(null=True,blank=True)
    services = models.JSONField()


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact Form"
        verbose_name_plural = "Contact Forms"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"
    





#----------------------------------------------------------New Carousel---------------------------------------------------------------

class CarouselModel(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='Carousel/')
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField()
    is_mobile = models.BooleanField(default=False)
    class Meta:
        ordering = ['order']
    def get_absolute_image_url(self, request):
        return request.build_absolute_uri(self.image.url)
    

#-----------------------------------------------------Carousel Log Model------------------------------------------------------------------


class CarouselLogModel(models.Model):
    carousel = models.ForeignKey(CarouselModel, on_delete=models.SET_NULL, related_name='carousel_log',null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carousel_log',null=True)
    action = models.CharField(max_length=100)
    description = models.TextField(null=True,blank=True)
    class Meta:
        ordering = ['-timestamp']

