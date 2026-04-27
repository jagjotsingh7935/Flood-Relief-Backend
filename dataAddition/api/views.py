from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from floodsApp.models import *
from django.db.models import Sum
from django.db.models import Count
from django.conf import settings
import os
import uuid
from urllib.parse import urljoin
from weasyprint import HTML
from django.http import HttpResponse
from .affectedvillagespdf import get_affected_villages_pdf_template

class AddNewDistrict(APIView):
    def post (self,request):
        
        state_id = request.data.get('state_id')
        district_name = request.data.get('name')

        try:
            state = State.objects.get(id=state_id)
        except State.DoesNotExist:
            return Response("State Does Not Exist",status=status.HTTP_404_NOT_FOUND)

        district = City.objects.create(
            state = state,
            name = district_name
        )

        response_data = {
            'district_id':district.id,
            'name':district.name
        }

        return Response(response_data,status=status.HTTP_201_CREATED)
    




class AddNewTehsil(APIView):
    def post (self,request):
        
        district_id = request.data.get('district_id')
        tehsil_name = request.data.get('name')

        try:
            district = City.objects.get(id=district_id)
        except City.DoesNotExist:
            return Response("District Does Not Exist",status=status.HTTP_404_NOT_FOUND)

        tehsil = Tehsil.objects.create(
            city = district,
            name = tehsil_name
        )

        response_data = {
            'tehsil_id':tehsil.id,
            'name':tehsil.name
        }

        return Response(response_data,status=status.HTTP_201_CREATED)
    




class AddNewVillage(APIView):
    def post (self,request):
        
        tehsil_id = request.data.get('tehsil_id')
        village_name = request.data.get('name')
        longitude_payload = request.data.get('longitude')
        latitude_payload = request.data.get('latitude')

        try:
            tehsil = Tehsil.objects.get(id=tehsil_id)
        except Tehsil.DoesNotExist:
            return Response("Tehsil Does Not Exist",status=status.HTTP_404_NOT_FOUND)
        


        if longitude_payload and latitude_payload:
            village = Village.objects.create(
            tehsil = tehsil,
            display_name = village_name,
            longitude = longitude_payload,
            latitude = latitude_payload
            )

        
        else:
            village_long_lat = Village.objects.filter(tehsil__id = tehsil_id).first()

            
            if village_long_lat and village_long_lat.longitude and village_long_lat.latitude:
                longitude = village_long_lat.longitude
                latitude = village_long_lat.latitude
            else:
                longitude = None
                latitude = None

            village = Village.objects.create(
                tehsil = tehsil,
                display_name = village_name,
                longitude = longitude,
                latitude = latitude
            )

        
        response_data = {
            'village_id':village.id,
            'display_name':village.display_name,
            'longitude':village.longitude,
            'latitude':village.latitude
        }

        return Response(response_data,status=status.HTTP_201_CREATED)
    





class TopCardsStats(APIView):
    def get(self, request):
        # Get all farmer forms
        farmer = FarmerForm.objects.all()
        farmer_count = farmer.count()

        # Sum up total land affected, amount needed, and amount received
        total_land_affected = farmer.aggregate(Sum('landAffected'))['landAffected__sum'] or 0
        total_amount_needed = farmer.aggregate(Sum('amount_needed'))['amount_needed__sum'] or 0
        total_amount_received = farmer.aggregate(Sum('amount_received'))['amount_received__sum'] or 0

        affected_areas_count = PersonData.objects.values('village_id').distinct().count()


        response_data = {
            'total_farmer_count': farmer_count,
            'total_land_affected': int(total_land_affected),  # Ensure integer output
            'total_amount_needed': int(total_amount_needed),  # Ensure integer output
            'total_amount_received': int(total_amount_received),  # Ensure integer output
            'affected_areas_count':affected_areas_count or '54',
            'relief_camps':'28'
        }

        return Response(response_data, status=status.HTTP_200_OK)
    


class AffectedVillagesPdf(APIView):
    def get(self, request):
        # Get unique villages with person data count
        affected_areas = PersonData.objects.values(
            'village_id',
            'village__display_name',
            'village__tehsil__name',
            'village__tehsil__city__name'
        ).annotate(
            person_count=Count('id')
        ).distinct()

        # Prepare data for PDF with SrNo
        data = [
            {
                'SrNo': index + 1,
                'village_id': area['village_id'],
                'village_name': area['village__display_name'],
                'tehsil_name': area['village__tehsil__name'],
                'city_name': area['village__tehsil__city__name'],
                'person_count': area['person_count']
            }
            for index, area in enumerate(affected_areas)
        ]

        # Render the template with data
        rendered_html = get_affected_villages_pdf_template(data, len(data))

        # Generate PDF
        pdf_file_name = f"affected_villages_report_{uuid.uuid4()}.pdf"
        pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'reports', pdf_file_name)
        os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
        HTML(string=rendered_html).write_pdf(pdf_file_path)

        # Generate absolute URL for the PDF
        pdf_url = urljoin(request.build_absolute_uri('/'), os.path.join(settings.MEDIA_URL, 'reports', pdf_file_name))

        return HttpResponse(pdf_url, content_type='text/plain')