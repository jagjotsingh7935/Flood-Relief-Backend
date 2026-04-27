from rest_framework import serializers
from accounts.models import *
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()




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
            except Admin.DoesNotExist:
                return None
    
   
    
            
    def get_profile_id(self, user):
        if user.is_admin:
            try:
                return user.admin.id
            except Admin.DoesNotExist:
                return None
            



class AdminCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Admin
        fields = ['id', 'email', 'is_active', 'first_name', 'last_name', 'full_name', 'avatar_image', 'phone_number', 'password']

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name') 
        phone_number = validated_data.pop('phone_number')
        password = validated_data.pop('password')
        validated_data['full_name'] = f"{first_name} {last_name}"

        print(f"DEBUG: Extracted email={email}, phone_number={phone_number}, first_name={first_name}, last_name={last_name}")

        if User.objects.filter(email=email).exists():
            print(f"DEBUG: Email {email} already exists in User model")
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        print(f"DEBUG: Creating User object for email={email}")
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_admin=True
        )

        print(f"DEBUG: User created with ID={user.id}")

        user.set_password(password)
        user.save()
        print(f"DEBUG: User password set and saved for {email}")

        print(f"DEBUG: Creating Admin object for user={user.id}")

        admin = Admin.objects.create(
            user=user,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            **validated_data
        )
        print(f"DEBUG: Admin created with ID={admin.id}")

        return admin

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['first_name'] = instance.user.first_name
        representation['last_name'] = instance.user.last_name
        representation['full_name'] = f"{instance.user.first_name} {instance.user.last_name}"
        return representation
    




class AdminDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Admin
        fields = ['id',
                  'email',
                  'first_name',
                  'last_name',
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
        model = Admin
        fields = ['admin_id', 'email', 'first_name', 'last_name', 'full_name', 'avatar_image','phone_number', 'is_active', 'created_at', 'last_updated']

    def get_admin_id(self, obj):
        return obj.id  
