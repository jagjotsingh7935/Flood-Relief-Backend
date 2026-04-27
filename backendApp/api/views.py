from django.shortcuts import get_object_or_404
from backendApp.models import *
from backendApp.api.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework import generics, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from backendApp.api.filters import *
from django.utils.timezone import now
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import viewsets, permissions

class UserListPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    
    def get_page_size(self, request):
        page_size = request.query_params.get('page_size')
        return int(page_size) if page_size else self.page_size

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'results': data,
            'filters': self.request.query_params.dict(),  # Include filters for debugging
        })
    


##########################
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("Received POST request with data:", request.data)
        serializer = self.get_serializer(data=request.data)
        print("Serializer initialized with data")

        try:
            print("Validating serializer...")
            serializer.is_valid(raise_exception=True)
            print("Serializer validation successful")
        except TokenError as e:
            print(f"Token error occurred: {e}")
            raise InvalidToken(e.args[0])

        user = serializer.user
        print(f"User retrieved from serializer: {user}")

        user.last_login = now()
        user.save(update_fields=['last_login'])
        print(f"Updated last_login for user: {user}")

        user_serializer = UserSerializer(user)
        print("User data serialized")

        response_data = {
            'accessToken': serializer.validated_data['access'],
            'refreshToken': serializer.validated_data['refresh'],
            'user': user_serializer.data
        }
        print("Response data prepared:", response_data)

        return Response(response_data, status=status.HTTP_200_OK)
        



class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)





class AdminSignUpView(generics.CreateAPIView):
    queryset = AdminFitness.objects.all()
    serializer_class = AdminCreateSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        UserLogFitness.objects.create(
            user=self.request.user,
            email=user.email,
            action='CREATE',
            details=f"New admin user created: {user.email}"
        )




class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdminFitness.objects.all()
    serializer_class = AdminDetailSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        instance = serializer.save()
        UserLogFitness.objects.create(
            user=self.request.user,
            email=instance.email,
            action='UPDATE',
            details=f"Admin user updated: {instance.email}"
        )

    def perform_destroy(self, instance):
        UserLogFitness.objects.create(
            user=self.request.user,
            email=instance.email,
            action='DELETE',
            details=f"Admin user deleted: {instance.email}"
        )
        super().perform_destroy(instance)




class AdminListView(generics.ListAPIView):
    queryset = AdminFitness.objects.all()
    serializer_class = AdminListSerializer
    pagination_class = UserListPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = AdminFilter
    search_fields = ['full_name', 'email', 'phone_number']
    



class BrandViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Brand instances.
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]   # adjust as needed
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Optional: filter by name (GET ?search=Nike)
    filterset_fields = ['name']
    search_fields = ['name']


##Frontend
class PublicBrandViewSet(viewsets.ReadOnlyModelViewSet):
  
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny] 
    lookup_field = 'id'
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Optional: add search & filter
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name'] 


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ['author']
    search_fields = ['text', 'author']

#Frontend
class PublicReviewViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    filterset_fields = ['author']
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['text', 'author']
    ordering_fields = ['created_at']
    ordering = ['-created_at']




class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['name']
    search_fields = ['name']

#Frontend
class PublicCertificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Certification.objects.all().order_by('name')
    serializer_class = CertificationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']




class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ['category', 'author']
    search_fields = ['title', 'excerpt', 'content', 'author']
    ordering_fields = ['date', 'created_at']


#Frontend
class PublicBlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.all().order_by('-date', '-created_at')
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'excerpt', 'content', 'author']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']



class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ['author', 'discount']
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['created_at']

#Frontend
class PublicBookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.all().order_by('title')
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['author', 'discount']
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']




class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ['name', 'position','title']
    search_fields = ['name', 'position', 'quote','title']


#Frontend
class PublicTestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.all().order_by('-created_at')
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['name', 'position','title']
    search_fields = ['name', 'position', 'quote','title']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class ContactFormViewSet(viewsets.ModelViewSet):
    queryset = ContactForm.objects.all().order_by('-created_at')
    serializer_class = ContactFormSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['name', 'email']
    search_fields = ['name', 'email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']




class PublicContactFormViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContactForm.objects.all().order_by('-created_at')
    serializer_class = ContactFormSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['name', 'email']
    search_fields = ['name', 'email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']







#------------------------------------------------------------New Carousel-------------------------------------------------------------------------


class CarouselCreateView(APIView):


    permission_classes = [IsAuthenticated]


    def post(self, request):
        user = request.user
        serializer = CarouselModelSerializer(data=request.data,context={'request': request})
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        CarouselLogModel.objects.create(
            user=user,
            carousel = serializer.instance,
            action='create',
            description='Carousel created successfully'
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

    def get(self,request):
        carousel = CarouselModel.objects.filter(is_mobile=False)
        serializer = CarouselModelSerializer(carousel, many=True,context={'request': request})
        return Response(serializer.data)
    



###

class CarouselFrontendView(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        carousel = CarouselModel.objects.filter(is_mobile=False)
        serializer = CarouselModelSerializer(carousel, many=True,context={'request': request})
        return Response(serializer.data)
    



class CarouselUpdateView(APIView):


    permission_classes = [IsAuthenticated]


    def get(self,request,pk):
        carousel = CarouselModel.objects.get(id=pk)
        serializer = CarouselModelSerializer(carousel, many=False,context={'request': request})
        return Response(serializer.data)
    

    def patch(self, request, pk):
        user = request.user
        carousel = CarouselModel.objects.get(id=pk)

        
        # Handle partial updates properly
        serializer = CarouselModelSerializer(
            carousel, 
            data=request.data, 
            partial=True,  # This is critical for PATCH requests
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        CarouselLogModel.objects.create(
            user=user,
            carousel = serializer.instance,
            action='update',
            description='Carousel updated successfully'
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def delete(self,request,pk):
        user = request.user
        carousel = CarouselModel.objects.get(id=pk)
        CarouselLogModel.objects.create(
            user=user,
            action='delete',
            description='Carousel deleted successfully' +'<..>' +'Carousel Title: '+ carousel.title
        )
        carousel.delete()
        return Response({"message": "Carousel deleted"}, status=status.HTTP_200_OK)
    


###

class CarouselDetailFrontendView(APIView):
    permission_classes = [AllowAny]
    def get(self,request,pk):
        carousel = CarouselModel.objects.get(id=pk)
        serializer = CarouselModelSerializer(carousel, many=False,context={'request': request})
        return Response(serializer.data)
    




def build_carousel_data(obj, request):
    """
    Manually builds the serialized representation of CarouselModel instance(s).
    Replicates exactly what the old CarouselMobileModelSerializer produced.
    """
    if hasattr(obj, '__iter__') and not hasattr(obj, 'pk'):  # queryset or list
        return [build_carousel_data(item, request) for item in obj]
    
    # Single instance
    image_url = None
    if obj.image:
        if request:
            image_url = request.build_absolute_uri(obj.image.url)
        else:
            image_url = obj.image.url

    return {
        'id': obj.id,
        'title': obj.title,
        'image': image_url,
        'created_at': obj.created_at,
        'order': obj.order,
        'description': obj.description,
        'is_mobile': obj.is_mobile,
    }


class CarouselCreateViewMobile(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Basic validation (adjust required fields as needed)
        data = request.data
        required_fields = ['title', 'order']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return Response(
                {"detail": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        carousel = CarouselModel.objects.create(
            title=data.get('title'),
            description=data.get('description', ''),
            order=data.get('order'),
            image=data.get('image'),  # DRF handles file upload
            is_mobile = True
        )

        CarouselLogModel.objects.create(
            user=user,
            carousel=carousel,
            action='create',
            description='Carousel created successfully'
        )

        response_data = build_carousel_data(carousel, request)
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request):
        carousel = CarouselModel.objects.filter(is_mobile=True).order_by('order')
        response_data = build_carousel_data(carousel, request)
        return Response(response_data)


class CarouselFrontendViewMobile(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        carousel = CarouselModel.objects.filter(is_mobile=True).order_by('order')
        response_data = build_carousel_data(carousel, request)
        return Response(response_data)


class CarouselUpdateViewMobile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        carousel = get_object_or_404(CarouselModel, id=pk)
        response_data = build_carousel_data(carousel, request)
        return Response(response_data)

    def patch(self, request, pk):
        user = request.user
        carousel = get_object_or_404(CarouselModel, id=pk)
        data = request.data

        # Partial update – only change provided fields
        if 'title' in data:
            carousel.title = data['title']
        if 'description' in data:
            carousel.description = data['description']
        if 'order' in data:
            carousel.order = data['order']
        if 'image' in data:
            carousel.image = data['image']  # Can be new file or null to clear

        carousel.save()

        CarouselLogModel.objects.create(
            user=user,
            carousel=carousel,
            action='update',
            description='Carousel updated successfully'
        )

        response_data = build_carousel_data(carousel, request)
        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        user = request.user
        carousel = get_object_or_404(CarouselModel, id=pk)

        CarouselLogModel.objects.create(
            user=user,
            carousel=carousel,
            action='delete',
            description=f'Carousel deleted successfully. Carousel Title: {carousel.title}'
        )
        carousel.delete()
        return Response({"message": "Carousel deleted"}, status=status.HTTP_200_OK)


class CarouselDetailFrontendViewMobile(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        carousel = get_object_or_404(CarouselModel, id=pk)
        response_data = build_carousel_data(carousel, request)
        return Response(response_data)