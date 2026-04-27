from rest_framework import serializers
from backendApp.models import *
# from password_generator import PasswordGenerator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction

from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()
# pwo = PasswordGenerator()
# pwo.maxlen = 8



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            try:
                user = User.objects.get(username__iexact=username)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass

        data = super().validate(attrs)
        self.user = self.user
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()


    class Meta:
        model=User
        fields=['id','profile_id','username', 'full_name', 'email', 'is_admin']

    def get_full_name(self, user):
        if user.is_admin:
            try:
                full_name = user.admin.full_name
                return full_name
            except AdminFitness.DoesNotExist:
                return None



    def get_profile_id(self, user):
        if user.is_admin:
            try:
                return user.admin.id
            except AdminFitness.DoesNotExist:
                return None



class AllUserListSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.SerializerMethodField()
    avatar_image = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    admin_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar_image', 'phone_number', 'is_active', 'created_at', 'last_updated', 'is_admin', 'admin_id']

    def get_profile(self, obj):
        if hasattr(obj, 'admin'):
            return obj.admin
        return None


    def get_full_name(self, obj):
        return self.get_profile(obj).full_name

    def get_avatar_image(self, obj):
        profile = self.get_profile(obj)
        if profile.avatar_image:
            return self.context['request'].build_absolute_uri(profile.avatar_image.url)
        return None

    def get_phone_number(self, obj):
        return self.get_profile(obj).phone_number

    def get_is_active(self, obj):
        return self.get_profile(obj).is_active

    def get_created_at(self, obj):
        return self.get_profile(obj).created_at

    def get_last_updated(self, obj):
        return self.get_profile(obj).last_updated

    def get_is_admin(self, obj):
        return hasattr(obj, 'admin')

    def get_admin_id(self, obj):
        if hasattr(obj, 'admin'):
            return obj.admin.id
        return None

  





class AdminCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = AdminFitness
        fields = ['id','email','is_active','full_name','avatar_image','phone_number']

    
    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email')
        full_name = validated_data.pop('full_name')
        phone_number = validated_data.pop('phone_number')

        print(f"DEBUG: Extracted email={email}, phone_number={phone_number}, full_name={full_name}")


        if User.objects.filter(email=email).exists():
            print(f"DEBUG: Email {email} already exists in User model")
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        print(f"DEBUG: Creating User object for email={email}")
        user = User.objects.create(
            username=email,
            email=email,
            full_name=full_name,
            is_admin=True
        )

        print(f"DEBUG: User created with ID={user.id}")

        # temp_password = pwo.generate()
        temp_password = 'abc'

        print(f"DEBUG: Generated temporary password for {email}")
        user.set_password(temp_password)
        user.save()
        print(f"DEBUG: User password set and saved for {email}")

        with open('passwords.csv', 'a') as file:
            file.write(f'\n{email},{temp_password}')
            print(f"DEBUG: Saved email and password to passwords.csv")

        print(f"DEBUG: Creating Admin object for user={user.id}")

        admin = AdminFitness.objects.create(
            user=user,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            **validated_data
        )
        print(f"DEBUG: Admin created with ID={admin.id}")


        
        return admin

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['full_name'] = instance.user.full_name
        return representation
    



class AdminDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AdminFitness
        fields = ['id',
                  'email',
                  'full_name',
                  'avatar_image',
                  'phone_number',
                  'is_active',
                  'created_at',
                  'last_updated',
                  ]



class AdminListSerializer(serializers.ModelSerializer):
    admin_id = serializers.SerializerMethodField()

    class Meta:
        model = AdminFitness
        fields = ['admin_id', 'email', 'full_name', 'avatar_image', 'phone_number', 'is_active', 'created_at', 'last_updated']

    def get_admin_id(self, obj):
        return obj.id  




class BrandSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(allow_empty_file=True, required=False, use_url=True)

    class Meta:
        model = Brand
        fields = ['id', 'name', 'color', 'logo','description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_logo(self, obj):
        if obj.logo and hasattr(obj.logo, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None
    


class ReviewSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(allow_empty_file=True, required=False, use_url=True)

    class Meta:
        model = Review
        fields = ['id', 'text', 'author', 'avatar', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None
    


class CertificationSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_empty_file=True, required=False, use_url=True)

    class Meta:
        model = Certification
        fields = ['id', 'name', 'image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    


class BlogPostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_empty_file=True, required=False, use_url=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'excerpt', 'content', 'image',
            'category', 'date', 'read_time', 'author',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class BookSerializer(serializers.ModelSerializer):
    # Accept dynamic image1, image2, ... fields from form-data
    image1 = serializers.ImageField(write_only=True, required=False)
    image2 = serializers.ImageField(write_only=True, required=False)
    image3 = serializers.ImageField(write_only=True, required=False)
    image4 = serializers.ImageField(write_only=True, required=False)
    # You can add more if needed (image5, etc.)

    # This will return URLs in the response
    images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'description',
            'discount',
            'bg_gradient',
            'image1', 'image2', 'image3', 'image4',  # write-only file fields
            'images',  # read-only: returns list of URLs after save
        ]
        extra_kwargs = {
            'title': {'required': True},
            'author': {'required': True},
        }

    def get_images(self, obj):
        request = self.context.get('request')
        image_objects = obj.images.all()
        if not image_objects and obj.image:
            image_objects = [obj.image]

        urls = []
        for img in image_objects:
            if img.image:
                url = img.image.url
                if request:
                    url = request.build_absolute_uri(url)
                urls.append(url)
        return urls

    def create(self, validated_data):
        # Extract image files
        image_files = []
        for key in ['image1', 'image2', 'image3', 'image4']:
            file = validated_data.pop(key, None)
            if file:
                image_files.append(file)

        # Create the book instance
        book = Book.objects.create(**validated_data)

        # Save each uploaded image as BookImage and attach to book
        primary_set = False
        for file in image_files:
            # Create BookImage instance
            book_image = BookImage.objects.create(image=file)
            
            # Add to ManyToMany
            book.images.add(book_image)
            
            # Set first image as primary (optional logic)
            if not primary_set:
                book.image = book_image
                primary_set = True

        book.save()
        return book
    
    
class TestimonialSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_empty_file=True, required=False, use_url=True)

    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'position', 'quote', 'image','title', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    



# class ContactFormSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = ContactForm
#         fields = ['id', 'name', 'email', 'project', 'services', 'created_at', 'updated_at']
#         read_only_fields = ['created_at', 'updated_at']



class ContactFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactForm
        fields = ['id', 'name', 'email', 'project', 'services', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Create the instance first
        contact = super().create(validated_data)

        # Send emails after successful creation
        try:
            self._send_user_confirmation_email(contact)
            self._send_admin_notification_email(contact)
        except Exception as e:
            print(f"Failed to send emails for ContactForm {contact.id}: {e}")
            # We don't raise here – the submission should still succeed even if email fails

        return contact

    def _send_user_confirmation_email(self, contact: ContactForm):
        subject = "Thank you for reaching out to Bob Chris Fitness!"
        message = f"""
        Hi {contact.name},

        Thank you for contacting Bob Chris – your personal fitness coach!

        We have received your inquiry and will get back to you within 24-48 hours.

        Here’s a copy of what you sent us:
        ———————————————
        Name: {contact.name}
        Email: {contact.email}
        Project/Details: {contact.project or 'Not provided'}
        Services interested in: {', '.join(contact.services) if isinstance(contact.services, list) else contact.services}
        ———————————————

        Let’s get you in the best shape of your life!

        Best regards,  
        Bob Chris  
        Metabolic Reset With Bob
        contact@metabolicresetwithbob.com
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[contact.email],
            fail_silently=False,
        )

    def _send_admin_notification_email(self, contact: ContactForm):
        subject = f"New Contact Form Submission – {contact.name}"
        services_str = ', '.join(contact.services) if isinstance(contact.services, list) else contact.services

        message = f"""
        A new contact form has been submitted:

        Name: {contact.name}
        Email: {contact.email}
        Project/Details: {contact.project or '—'}
        Services: {services_str}
        Submitted at: {contact.created_at}

        Reply directly to {contact.email} to get in touch.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.ADMIN_EMAIL],   # your env variable
            fail_silently=False,
        )





#-------------------------------------------------------New Carousel-------------------------------------------------------------

class CarouselModelSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CarouselModel
        fields = ['id', 'title', 'image', 'created_at', 'order', 'description']
    
    def get_image_url(self, obj):  # Renamed to match SerializerMethodField convention
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None if not obj.image else obj.image.url
    


class CarouselMobileModelSerializer(serializers.ModelSerializer):

    is_mobile = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = CarouselModel
        fields = ['id', 'title', 'image', 'created_at', 'order', 'description','is_mobile']
    
    def get_image_url(self, obj):  # Renamed to match SerializerMethodField convention
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None if not obj.image else obj.image.url
    


    


class CarouselLogModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = CarouselLogModel
            fields = '__all__'
    

