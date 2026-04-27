from rest_framework_simplejwt.views import  TokenRefreshView, TokenVerifyView
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'certifications', CertificationViewSet, basename='certification')
router.register(r'blogposts', BlogPostViewSet, basename='blogpost')
router.register(r'books', BookViewSet, basename='book')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'contactform', ContactFormViewSet, basename='contactform')




router.register(r'brands-public', PublicBrandViewSet, basename='brand-public')
router.register(r'reviews-public', PublicReviewViewSet, basename='review-public')
router.register(r'certifications-public', PublicCertificationViewSet, basename='certification-public')
router.register(r'blogposts-public', PublicBlogPostViewSet, basename='blogpost-public')
router.register(r'books-public', PublicBookViewSet, basename='book-public')
router.register(r'testimonials-public', PublicTestimonialViewSet, basename='testimonial-public')
router.register(r'contactform-public', PublicContactFormViewSet, basename='contactform-public')


urlpatterns = [

    path('', include(router.urls)),

    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout-view'),
    
    path('me/', CurrentUserView.as_view(), name='current-user'),

    

    path('signup/admin/', AdminSignUpView.as_view(), name='admin-signup'),
    path('admin/<int:pk>/', AdminDetailView.as_view(), name='admin-detail'),
    path('admin/', AdminListView.as_view(), name='admin-list'),



    

#--------------------------------------------------------Create and show the carousel---------------------------------------------------------

    path('Carousel/', CarouselCreateView.as_view(), name='images_list'),

    path('Carousel/mobile/', CarouselCreateViewMobile.as_view(), name='images_list_mobile'),



#--------------------------------------------------------Show the carousel on Frontend----------------------------------------------------------
    path('CarouselFrontend/',CarouselFrontendView().as_view(), name='image-list-frontend'),

    path('CarouselFrontend/mobile/',CarouselFrontendViewMobile().as_view(), name='image-list-frontend_mobile'),



#--------------------------------------------------------Update and show the particular carousel---------------------------------------------
    path('Carousel/<int:pk>/', CarouselUpdateView.as_view(), name='images_detail'),

    path('Carousel/<int:pk>/mobile/', CarouselUpdateViewMobile.as_view(), name='images_detail_mobile'),



#------------------------------------------------------Show the particular carousel------------------------------------------------------------
    path('CarouselFrontendDetail/<int:pk>/', CarouselDetailFrontendView.as_view(), name='images_detail'),

    path('CarouselFrontendDetail/<int:pk>/mobile/', CarouselDetailFrontendViewMobile.as_view(), name='images_detail_mobile'),


]