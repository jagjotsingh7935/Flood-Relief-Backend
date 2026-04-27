from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [



    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout-view'),
    
    path('me/', CurrentUserView.as_view(), name='current-user'),
    
    path('signup/admin/', AdminSignUpView.as_view(), name='admin-signup'),
    path('admin/<int:pk>/', AdminDetailView.as_view(), name='admin-detail'),
    path('admin/', AdminListView.as_view(), name='admin-list'),


    path('scrap/locations/', ScrapeLocationAPIView.as_view(), name='scrap-locations'),



]