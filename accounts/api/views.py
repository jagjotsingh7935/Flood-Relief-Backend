from accounts.models import *
from accounts.api.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from rest_framework import generics, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from accounts.api.filters import *
from django.utils.timezone import now
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated


import requests
from floodsApp.models import State, City, Tehsil, Village  




class UserListPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100  # Optional: Set a maximum page size to prevent abuse

    def get_page_size(self, request):
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size:
            try:
                return min(int(page_size), self.max_page_size) if self.max_page_size else int(page_size)
            except (ValueError, TypeError):
                pass  # Fallback to default page_size if invalid
        return self.page_size

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page.paginator.per_page,
            'results': data
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
    



class LogoutView(generics.GenericAPIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)

class AdminSignUpView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Admin.objects.all()
    serializer_class = AdminCreateSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        
        UserLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            email=user.email,
            action='CREATE',
            details=f"New admin user created: {user.email}"
        )





class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Admin.objects.all()
    serializer_class = AdminDetailSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        UserLog.objects.create(
            user=self.request.user,
            email=instance.email,
            action='UPDATE',
            details=f"Admin user updated: {instance.email}"
        )

    def perform_destroy(self, instance):
        UserLog.objects.create(
            user=self.request.user,
            email=instance.email,
            action='DELETE',
            details=f"Admin user deleted: {instance.email}"
        )
        super().perform_destroy(instance)






class AdminListView(generics.ListAPIView):
    queryset = Admin.objects.all()
    serializer_class = AdminListSerializer
    pagination_class = UserListPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = AdminFilter
    search_fields = ['full_name', 'email', 'phone_number']
    


class ScrapeLocationAPIView(APIView):
    def get(self, request):
        # Get or create the State for Punjab
        print("Attempting to get or create State: Punjab")
        state, _ = State.objects.get_or_create(name='Punjab')
        print(f"State 'Punjab' retrieved/created with ID: {state.id}")

        # Fetch districts for state_id=1 (Punjab)
        district_url = 'https://deals.sarkarekhalsa.org/v1/location/list_district/1'
        print(f"Fetching districts from URL: {district_url}")
        district_response = requests.get(district_url)
        district_data = district_response.json()
        print(f"Districts response status: {district_response.status_code}, Data: {district_data}")

        if not district_data.get('success', False):
            print("Failed to fetch districts, returning error response")
            return Response({'error': 'Failed to fetch districts'}, status=400)

        added_cities = 0
        added_tehsils = 0
        added_villages = 0

        for dist in district_data['data']:
            print(f"\nProcessing district: {dist['district_name']} (ID: {dist['district_id']})")
            # Create City (district as city)
            city, created = City.objects.get_or_create(
                state=state,
                name=dist['district_name'],
                defaults={'is_active': True}
            )
            action = "Created" if created else "Already exists"
            print(f"City {city} {action}, ID: {city.id}")
            if created:
                added_cities += 1

            # Fetch blocks (tehsils) for this district_id
            block_url = f'https://deals.sarkarekhalsa.org/v1/location/list_block/{dist["district_id"]}'
            print(f"Fetching blocks for district ID {dist['district_id']} from URL: {block_url}")
            block_response = requests.get(block_url)
            block_data = block_response.json()
            print(f"Blocks response status: {block_response.status_code}, Data: {block_data}")

            if not block_data.get('success', False):
                print(f"Failed to fetch blocks for district ID {dist['district_id']}, skipping")
                continue

            for block in block_data['data']:
                print(f"\nProcessing block: {block['block_name']} (ID: {block['block_id']})")
                # Create Tehsil (block as tehsil)
                tehsil, created = Tehsil.objects.get_or_create(
                    city=city,
                    name=block['block_name'],
                    defaults={'is_active': True}
                )
                action = "Created" if created else "Already exists"
                print(f"Tehsil {tehsil} {action}, ID: {tehsil.id}")
                if created:
                    added_tehsils += 1

                # Fetch places (villages) for this block_id
                place_url = f'https://deals.sarkarekhalsa.org/v1/location/list_place/{block["block_id"]}'
                print(f"Fetching places for block ID {block['block_id']} from URL: {place_url}")
                place_response = requests.get(place_url)
                place_data = place_response.json()
                print(f"Places response status: {place_response.status_code}, Data: {place_data}")

                if not place_data.get('success', False):
                    print(f"Failed to fetch places for block ID {block['block_id']}, skipping")
                    continue

                for place in place_data['data']:
                    print(f"Processing place: {place['place_name']} (ID: {place['place_id']})")
                    # Create Village, using block's lat/long as approximate, pin_code as empty
                    village, created = Village.objects.get_or_create(
                        tehsil=tehsil,
                        display_name=place['place_name'],
                        pin_code='',
                        defaults={
                            'longitude': block.get('longitude', None),
                            'latitude': block.get('latitude', None),
                            'is_active': True
                        }
                    )
                    action = "Created" if created else "Already exists"
                    print(f"Village {village.display_name} {action}, ID: {village.id}")
                    if created:
                        added_villages += 1

        print(f"\nSummary - Added: {added_cities} cities, {added_tehsils} tehsils, {added_villages} villages")
        return Response({
            'message': 'Data scraped and added successfully',
            'added_cities': added_cities,
            'added_tehsils': added_tehsils,
            'added_villages': added_villages
        })






class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)