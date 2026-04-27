from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from django.utils import timezone
from django.db.models import Q
from .google_api import schedule_meeting
from django.conf import settings
import razorpay
from rest_framework.generics import ListAPIView

from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime, timedelta
import os
from rest_framework.pagination import PageNumberPagination


from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import time
from django.contrib.auth import authenticate, login
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout




from django.http import FileResponse
from django.conf import settings
import os



from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.http import HttpResponseRedirect, HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
import json
from django.core.cache import cache


from django.db.models import Prefetch


from django.core.mail import EmailMessage




User = get_user_model()


# class FeesCreateView(APIView):

#     permission_classes = [IsAuthenticated]

#     def post(self,request):
#         serializer = FeesModelSerializer(data=request.data)
        
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class FeesCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Extract fee amounts
        amount_online = request.data.get('amountOnline')

        if not amount_online:
            return Response(
                {"error": "amountOnline and amountOffline are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount_online = int(amount_online)
        except (TypeError, ValueError):
            return Response(
                {"error": "amountOnline and amountOffline must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract program fields (allow null/blank as per model)
        title = request.data.get('title', '').strip() or None
        description = request.data.get('description', '').strip() or None
        discount = request.data.get('discount', '').strip() or None

        # Create a new Program every time (or change to get_or_create if you prefer reuse)
        program = Program.objects.create(
            title=title,
            description=description,
            discount=discount
        )

        # Collect uploaded image files
        files = request.FILES.getlist('image')  # Recommended: multiple files with key "image"

        if not files:
            # Fallback for image[0], image[1], etc.
            i = 0
            while True:
                file_key = f'image[{i}]'
                file = request.FILES.get(file_key)
                if not file:
                    break
                files.append(file)
                i += 1

        uploaded_images = []
        for image_file in files:
            if not image_file.content_type.startswith('image/'):
                return Response(
                    {"error": f"File {image_file.name} is not a valid image."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            program_image = ProgramImage.objects.create(image=image_file)
            uploaded_images.append(program_image)

        # Add all images to the program
        if uploaded_images:
            program.images.add(*uploaded_images)

        # Create the Fees entry
        fees = FeesModel.objects.create(
            amountOnline=amount_online,
            program=program
        )

        # Response with created data
        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "created_at": fees.created_at.isoformat(),
            "program": {
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "discount": program.discount,
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                    }
                    for img in program.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    

# class FeesShowView(APIView):


#     def get(self, request):

        
#         try:
#             fees = FeesModel.objects.all().order_by('-created_at')
#             serializer = FeesModelSerializer(fees)
#             return Response(serializer.data)
#         except FeesModel.DoesNotExist:
#             return Response({"error": "No fee configuration found"}, status=status.HTTP_404_NOT_FOUND)



class FeesDetailView(APIView):
    """
    Retrieve, update or delete a Program along with its linked FeesModel entry.
    Now operates Program-wise: endpoint uses Program ID (pk).
    Response structure is identical to the original FeesDetailView.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # pk is now the Program ID
        program = get_object_or_404(Program, pk=pk)

        # Get the associated Fees via reverse relation
        # In your model: program = models.ForeignKey(Program, related_name='program')
        # So reverse accessor is .program (a manager)
        fees_qs = getattr(program, 'program', None)

        if not fees_qs or not fees_qs.exists():
            return Response(
                {"error": "This Program has no associated fees."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Assuming one-to-one relationship: take the first (and only) fees
        fees = fees_qs.first()

        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat() if fees.created_at else None,
            "program": {
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "discount": program.discount,
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                        "alt_text": img.alt_text or "",
                        "uploaded_at": img.uploaded_at.isoformat()
                    }
                    for img in program.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        # pk is now Program ID
        program = get_object_or_404(Program, pk=pk)

        fees_qs = getattr(program, 'program', None)
        if not fees_qs or not fees_qs.exists():
            return Response(
                {"error": "This Program has no associated fees to update."},
                status=status.HTTP_404_NOT_FOUND
            )
        fees = fees_qs.first()

        # Extract and validate fee amounts
        amount_online = request.data.get('amountOnline')
        amount_offline = request.data.get('amountOffline')

        if amount_online is None and amount_offline is None:
            return Response(
                {"error": "At least one of amountOnline or amountOffline is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount_online is not None:
            try:
                fees.amountOnline = int(amount_online)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOnline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if amount_offline is not None:
            try:
                fees.amountOffline = int(amount_offline)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOffline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        fees.save()

        # Update program fields
        title = request.data.get('title', '').strip() or None
        description = request.data.get('description', '').strip() or None
        discount = request.data.get('discount', '').strip() or None

        if title is not None:
            program.title = title
        if description is not None:
            program.description = description
        if discount is not None:
            program.discount = discount
        program.save()

        # Handle image removals
        remove_images_str = request.data.get('remove_images')
        if remove_images_str:
            try:
                remove_ids = json.loads(remove_images_str)
                if not isinstance(remove_ids, list):
                    raise ValueError
                images_to_remove = ProgramImage.objects.filter(id__in=remove_ids, books=program)
                for img in images_to_remove:
                    img.image.delete(save=False)  # Delete file from storage
                    img.delete()
                program.images.remove(*images_to_remove)
            except (json.JSONDecodeError, ValueError):
                return Response(
                    {"error": "remove_images must be a valid JSON list of image IDs."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Collect new uploaded images
        files = request.FILES.getlist('image')
        if not files:
            # Fallback support for image[0], image[1], etc.
            i = 0
            while True:
                file_key = f'image[{i}]'
                file = request.FILES.get(file_key)
                if not file:
                    break
                files.append(file)
                i += 1

        uploaded_images = []
        for image_file in files:
            if not image_file.content_type.startswith('image/'):
                return Response(
                    {"error": f"File {image_file.name} is not a valid image."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            program_image = ProgramImage.objects.create(image=image_file)
            uploaded_images.append(program_image)

        if uploaded_images:
            program.images.add(*uploaded_images)

        # Response with updated data (same structure as original)
        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat(),
            "program": {
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "discount": program.discount,
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                    }
                    for img in program.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        # pk is now Program ID
        program = get_object_or_404(Program, pk=pk)

        fees_qs = getattr(program, 'program', None)
        if not fees_qs or not fees_qs.exists():
            return Response(
                {"error": "This Program has no associated fees to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

        fees = fees_qs.first()
        fees.delete()

        return Response(
            {"message": "Program fees deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )



class FeesDelete(APIView):
    
    def delete(self, request, pk):
        # pk is now Program ID
        program = get_object_or_404(Program, pk=pk)

        fees_qs = getattr(program, 'program', None)
        if not fees_qs or not fees_qs.exists():
            return Response(
                {"error": "This Program has no associated fees to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

        fees = fees_qs.first()
        fees.delete()

        return Response(
            {"message": "Program fees deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
       

class FeesShowView(ListAPIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    queryset = FeesModel.objects.select_related('program').prefetch_related('program__images')
    # No serializer needed since we're building response manually

    def list(self, request):
        # Start from Program model, only those with at least one Fees entry
        # Reverse relation: FeesModel has ForeignKey to Program with related_name='program'
        # So reverse is program.program (manager)
        programs_with_fees = Program.objects.filter(program__isnull=False).distinct() \
            .prefetch_related('images') \
            .prefetch_related(
                Prefetch(
                    'program',  # reverse relation to FeesModel
                    queryset=FeesModel.objects.order_by('-created_at')  # latest fees first
                )
            ) \
            .order_by('-program__created_at')  # order by most recent fee

        data = []

        for program in programs_with_fees:
            # Get the most recent (or only) fees entry
            fees = program.program.first()  # reverse relation

            if not fees:
                continue  # safety check

            images = [
                {
                    "id": img.id,
                    "url": request.build_absolute_uri(img.image.url),
                    "alt_text": img.alt_text or "",
                }
                for img in program.images.all()
            ]

            data.append({
                "fees_id": fees.id,
                "amountOnline": fees.amountOnline,
                "amountOffline": fees.amountOffline,
                "created_at": fees.created_at.isoformat() if fees.created_at else None,
                "program": {
                    "id": program.id,
                    "title": program.title,
                    "description": program.description,
                    "discount": program.discount,
                    "images": images
                }
            })

        return Response(data, status=status.HTTP_200_OK)


class FeesShowBackendView(APIView):


    def get(self, request):
        try:
            fees = FeesModel.objects.latest('id')
            serializer = FeesModelSerializer(fees)
            return Response(serializer.data)
        except FeesModel.DoesNotExist:
            return Response({"error": "No fee configuration found"}, status=status.HTTP_404_NOT_FOUND)
        
        
class FeesShowAllView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        fees = FeesModel.objects.all()
        serializer = FeesModelSerializer(fees, many=True)
        return Response(serializer.data)
    


#-----------------------------------------------------------------user-----------------------------------------------------------
class UserSlotView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print("[DEBUG] Incoming POST request with data:", request.data)
        serializer = UserSlotSerializer(data=request.data)
        if not serializer.is_valid():
            print("[ERROR] Serializer validation failed:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            # First save the user_slot
            user_slot = serializer.save()
            
            # Then set payment status based on booking type
            if user_slot.isOnline:
                user_slot.payment_status = 'on hold'
                user_slot.save()
                print("[DEBUG] Online user slot created successfully with on hold status:", user_slot.id)
            elif user_slot.isOffline:
                user_slot.payment_status = 'on hold'
                user_slot.save()
                print("[DEBUG] Offline user slot created successfully with success status:", user_slot.id)
            
            UserSlotLogModel.objects.create(
                user=user,
                userSlot=user_slot,
                action='create',
                description='User Slot Created'
            )
            print("[DEBUG] Log entry created for user slot creation.")
            
            self._send_confirmation_email(user_slot)
            print("[DEBUG] Confirmation email sent successfully.")


            

            ##########################################
        
           
            
            return Response({
                'user_slot': UserSlotSerializer(user_slot).data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("[ERROR] Failed to process request:", str(e))
            return Response(
                {"error": f"Failed to process request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def put(self, request, pk=None):
        user = request.user
        print("[DEBUG] Incoming PUT request with data:", request.data, "for slot ID:", pk)
        if not pk:
            return Response({"error": "Slot ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_slot = UserSlot.objects.get(pk=pk)
            serializer = UserSlotSerializer(user_slot, data=request.data, partial=True)
            if not serializer.is_valid():
                print("[ERROR] Serializer validation failed:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if payment_status is being updated to 'pending'
            if 'payment_status' in request.data and request.data['payment_status'] == 'pending':
                # Reset the meet_link and make the slot available again
                user_slot.meet_link = None
                user_slot.payment_status = 'pending'
                user_slot.save()
                
                UserSlotLogModel.objects.create(
                    user=user,
                    userSlot=user_slot,
                    action='update',
                    description='User Slot Updated - Payment status set to pending, slot made available again'
                )
                
                return Response({
                    'message': 'Slot updated successfully, payment status set to pending, and slot made available again',
                    'status': 'success',
                }, status=status.HTTP_200_OK)
            
            updated_slot = serializer.save()
            print("[DEBUG] User slot updated successfully:", updated_slot.id)
            
            UserSlotLogModel.objects.create(
                user=user,
                userSlot=updated_slot,
                action='update',
                description='User Slot Updated'
            )
            print("[DEBUG] Log entry created for user slot update.")
            
            if updated_slot.isOnline and (
                'startTime' in request.data or
                'endTime' in request.data or
                'date' in request.data
            ):
                try:
                    meet_link = self._generate_meet_link(updated_slot)
                    print(f"[DEBUG] Updated slot: {updated_slot}")
                    print(f"[DEBUG] Meet link: {meet_link}")                    
                    updated_slot.meet_link = meet_link
                    updated_slot.save()
                    print("[DEBUG] Meeting link regenerated successfully:", meet_link)
                except Exception as e:
                    if "Redirect to Google OAuth" in str(e):
                        return Response({
                            'message': 'OAuth authentication required',
                            'status': 'redirect',
                            'redirect_url': str(e).split(": ")[1]
                        }, status=status.HTTP_302_FOUND)
                    print("[ERROR] Meet link regeneration failed:", str(e))
                    return Response({
                        'message': 'Slot updated but meet link regeneration failed',
                        'status': 'success',
                        'meet_link_status': 'failed',
                        'meet_link_error': str(e)
                    }, status=status.HTTP_200_OK)
            else:
                print("[DEBUG] No need to regenerate meet link as slot is not online or required fields are not updated.")
                
        # Send updated confirmation email for both online and offline slots
            self._updated_confirmation_email(updated_slot)
            print("[DEBUG] Update confirmation email sent successfully.")

        
            return Response(UserSlotSerializer(updated_slot).data, status=status.HTTP_200_OK)
        except UserSlot.DoesNotExist:
            print("[ERROR] Slot not found for ID:", pk)
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("[ERROR] Failed to update slot:", str(e))
            return Response(
                {"error": f"Failed to update slot: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_meet_link(self, user_slot):
        print("[DEBUG] Generating meet link for slot ID:", user_slot.id)
        meeting_data = {
            'firstName': user_slot.firstName,
            'lastName': user_slot.lastName,
            'email': user_slot.email,
            'isOnline': user_slot.isOnline,
            'isOffline': user_slot.isOffline,
            'startTime': user_slot.startTime,
            'endTime': user_slot.endTime,
            'date': user_slot.date,
            'message': user_slot.message,
            'meet_link': user_slot.meet_link,
            'created_at': user_slot.created_at,
            'payment_status': user_slot.payment_status,
        }
        try:
            return schedule_meeting(meeting_data)
        except Exception as e:
            if "Redirect to Google OAuth" in str(e):
                raise Exception(f"Redirect to Google OAuth: {str(e).split(': ')[1]}")
            raise e
    
    def _send_confirmation_email(self, user_slot, is_update=False):
        try:
            print("[DEBUG] Sending confirmation email to:", user_slot.email)
            subject = "Booking Confirmation Update" if is_update else "Booking Status"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user_slot.email]

            fee_config = FeesModel.objects.latest('id')
            amount = fee_config.amountOnline if user_slot.isOnline else fee_config.amountOffline
            
            # Common CSS styles for both email templates
            styles = """
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
                
                body {
                    font-family: 'Roboto', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                .header {
                    
                    text-align: center;
                    padding: 20px;
                }
                .header h1{
                    color: #026277
                }
                .header img {
                    max-width: 300px;
                    height: auto;
                }
                .content {
                    padding: 30px;
                    background-color: #ffffff;
                    border-top: 4px solid #026277
                }
                .details {
                    border-left: 4px solid #026277;
                    background-color: #f9f9f9;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                }
                .details p {
                    margin: 10px 0;
                    color: #555;
                }
                .details strong {
                    color: #026277;
                    min-width: 100px;
                    display: inline-block;
                }
                .system-notice {
                    font-family: 'Courier New', monospace;
                    color: #666;
                    font-size: 0.9em;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }
                .footer {
                    background-color: #f4f4f4;
                    text-align: center;
                    padding: 20px;
                    font-size: 0.9em;
                    color: #777;
                }
                .important-notice {
                    color: #666666;
                    font-weight: bold;
                    margin: 15px 0;
                    text-align: center;
                }
            """

            consultation_type = "online" if user_slot.isOnline else "offline"
            amount_text = f"<p><strong>Consultation Fee:</strong> ₹{amount}</p>" if amount else ""
            
            message = f"""
            <html>
                <head>
                    <style>{styles}</style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <img src="https://metabolicresetwithbob.com/assets/Logo-DFOA3T0r.png" alt="Metabolic Reset With Bob">
                            <h1>Consultation {subject}</h1>
                        </div>
                        <div class="content">
                            <p>Dear {user_slot.firstName},</p>
                            <p>Your {consultation_type} consultation slot has been put on hold. Please complete the payment process to confirm your booking.</p>
                            
                            <div class="details">
                                <p><strong>Date:</strong> {user_slot.date.strftime('%Y-%m-%d')}</p>
                                <p><strong>Time:</strong> {user_slot.startTime.strftime('%I:%M %p')} - {user_slot.endTime.strftime('%I:%M %p')}</p>
                                {amount_text}
                            </div>

            
                            
                            <p class="important-notice">Note: The consultation fee is non-refundable but can be rescheduled.</p>
                        </div>
                        <div class="footer">
                            <p>Best regards,</p>
                            <p><strong>Bob Chris</strong></p>
                            <p>Metabolic Reset With Bob</p>
                            <div class="system-notice">
                                This is a system-generated email. Please do not reply to this message.
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            send_mail(subject, message, from_email, recipient_list, fail_silently=False, html_message=message)
            print("[DEBUG] Email sent successfully to:", user_slot.email)
        except Exception as e:
            print("[ERROR] Failed to send confirmation email:", str(e))


    def _updated_confirmation_email(self, user_slot, is_update=True):
        try:
            print("[DEBUG] Sending update confirmation email to:", user_slot.email)
            subject = "Booking Update Confirmation"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user_slot.email]
            
            # Updated CSS and HTML template
            styles = """
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
                
                body {
                    font-family: 'Roboto', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                .header {
                
                    text-align: center;
                    padding: 20px;
                }

                .header h1{
                    color: #026277;
                }
                .header img {
                    max-width: 300px;
                    height: auto;
                    
                }
                .content {
                    padding: 30px;
                    background-color: #ffffff;
                    border-top: 4px solid #026277

                }
                .details {
                    background-color: #f9f9f9;
                    border-left: 4px solid #026277;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                }
                .details p {
                    margin: 10px 0;
                    color: #555;
                }
                .details strong {
                    color: #026277;
                    min-width: 100px;
                    display: inline-block;
                }
                .meeting-link {
                    display: block;
                    text-align: center;
                    margin: 20px 0;
                }
                .meeting-link a {
                    background-color: #026277;
                    color: white;
                    text-decoration: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    transition: background-color 0.3s ease;
                }
                .system-notice {
                    font-family: 'Courier New', monospace;
                    color: #666;
                    font-size: 0.9em;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }
                .footer {
                    background-color: #f4f4f4;
                    text-align: center;
                    padding: 20px;
                    font-size: 0.9em;
                    color: #777;
                }

                .clinic-info {
                    background-color: #e8f5e9;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 20px;
                    text-align: center;
                }
                .important-notice {
                    color: #666666;
                    font-weight: bold;
                    margin: 15px 0;
                    text-align: center;
                }
                .important-notice2 {
                    color: #666666;
                    
                    margin: 12px 0;
                    text-align: center;
                
                }
            """

            consultation_type = "online" if user_slot.isOnline else "offline"
            meeting_link = f"<div class='meeting-link'><a href='{user_slot.meet_link}'>Join Meeting</a></div>" if user_slot.isOnline else ""

            # Conditional content based on appointment type
            if user_slot.isOnline:
                specific_content = """
                <p class="important-notice2">Please ensure you have a stable internet connection and are in a quiet environment for your consultation. If you need to reschedule, please contact our office at least 24 hours in advance.</p>
                <p class="important-notice">Note: The consultation fee is non-refundable but can be rescheduled.</p>
                """
            else:
                specific_content = """
                <div class="clinic-info">
                    <p>Please arrive at our clinic 10 minutes before your scheduled time.</p>
                    <p><strong>Clinic Address:</strong> H.NO.1920, Sector 34-D, (Near Radio Station)
                Chandigarh - 160034, INDIA</p>
                </div>
                
                <p class="important-notice2">We look forward to providing you with personalized homeopathic care.</p>
                <p class="important-notice">Note: The consultation fee is non-refundable but can be rescheduled.</p>
                """
                
            message = f"""
            <html>
                <head>
                    <style>{styles}</style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <img src="https://metabolicresetwithbob.com/assets/Logo-DFOA3T0r.png" alt="Metabolic Reset With Bob">
                            <h1>Consultation Update Confirmation</h1>
                        </div>
                        <div class="content">
                            <p>Dear {user_slot.firstName},</p>
                            <p>Your {consultation_type} consultation details have been updated:</p>
                            
                            <div class="details">
                                <p><strong>New Date:</strong> {user_slot.date.strftime('%Y-%m-%d')}</p>
                                <p><strong>New Time:</strong> {user_slot.startTime.strftime('%I:%M %p')} - {user_slot.endTime.strftime('%I:%M %p')}</p>
                            </div>

                            {meeting_link if user_slot.isOnline else ""}
                            
                            {specific_content}

                        </div>
                        <div class="footer">
                            <p>Best regards,</p>
                            <p><strong>Bob Chris</strong></p>
                            <p>Metabolic Reset With Bob</p>
                            <div class="system-notice">
                                This is a system-generated email. Please do not reply to this message.
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
                
            send_mail(subject, message, from_email, recipient_list, fail_silently=False, html_message=message)
            print("[DEBUG] Update confirmation email sent successfully to:", user_slot.email)
        except Exception as e:
            print("[ERROR] Failed to send update confirmation email:", str(e))


# Delete For only pending payment status

    def delete(self, request, pk=None):
        user = request.user
        print("[DEBUG] Incoming DELETE request for slot ID:", pk)
        
        if not pk:
            return Response({"error": "Slot ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_slot = UserSlot.objects.get(pk=pk)
            
            # Check if the payment_status is 'pending'
            if user_slot.payment_status != 'pending':
                return Response(
                    {"error": "Cannot delete slot. Payment status is not 'pending'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Log the deletion
            UserSlotLogModel.objects.create(
                user=user,
                userSlot=user_slot,
                action='delete',
                description=f'User Slot Deleted - Slot ID: {user_slot.id}, Payment Status: {user_slot.payment_status}'
            )
            
            # Delete the slot
            user_slot.delete()
            
            return Response(
                {"message": "Slot deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except UserSlot.DoesNotExist:
            print("[ERROR] Slot not found for ID:", pk)
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            print("[ERROR] Failed to delete slot:", str(e))
            return Response(
                {"error": f"Failed to delete slot: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserSlotFrontendView(APIView):


    permission_classes = [AllowAny]


    def post(self, request):

        fees_id = request.data.get('fees_id')
        serializer = UserSlotSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Wrap the entire operation in a transaction
        with transaction.atomic():
            try:
                # Save the user slot
                user_slot = serializer.save()
            
                try:
                    fee_config = FeesModel.objects.get(id=fees_id)
                except FeesModel.DoesNotExist:
                    return Response({"error": "Invalid fees_id: Fee configuration not found"}, status=status.HTTP_400_BAD_REQUEST)
                amount_online = fee_config.amountOnline
                amount_offline = fee_config.amountOffline

                
                # Initialize Razorpay client
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                client.set_app_details({
                    "title": "Django",
                    "version": "5.1.4"
                })                
                
                # Set amount based on meeting type
                amount = amount_online if user_slot.isOnline else amount_offline  # ₹500 for online, ₹1000 for offline

                print("####################################################################################",amount)
                
                # Create Razorpay order
                razorpay_order = client.order.create({
                    'amount': int(amount * 100),  # Amount in paise
                    'currency': 'INR',
                    'payment_capture': 1,
                    'notes': {
                        'user_slot_id': user_slot.id,
                        'name': f"{user_slot.firstName} {user_slot.lastName}",
                        'email': user_slot.email,
                        'phone': user_slot.phoneNumber
                    }
                })


                
                # Create payment record
                payment = Payment.objects.create(
                    user_slot=user_slot,
                    razorpay_order_id=razorpay_order['id'],
                    amount=amount
                )
                
                return Response({
                    'user_slot': UserSlotSerializer(user_slot).data,
                    'payment': {
                        'order_id': razorpay_order['id'],
                        'amount': amount,
                        'currency': 'INR'
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # The transaction will automatically roll back in case of any exception
                return Response(
                    {"error": f"Failed to process request: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class UserShowView(APIView):


    permission_classes = [IsAuthenticated]


    def get(self, request):
        slot = UserSlot.objects.all()
        serializer = UserSlotSerializer(slot, many=True,context={'request': request})
        return Response(serializer.data)
    

class UserShow_filterView(APIView):


    permission_classes = [IsAuthenticated]


    def get(self, request):
        first_name = request.query_params.get('firstName', '').strip()
        last_name = request.query_params.get('lastName', '').strip()
        
        queryset = UserSlot.objects.all()
        
        if first_name:
            queryset = queryset.filter(firstName__iexact=first_name)
        if last_name:
            queryset = queryset.filter(lastName__iexact=last_name)

        if not queryset.exists():
            return Response(
                {"message": "No records found matching the search criteria"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSlotSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

#---------------------------------------------------------------Doctor-------------------------------------------------------------------

class DoctorScheduleTemplateView(APIView):


    # permission_classes=[IsAuthenticated]


    def post(self, request):
        user = request.user
        serializer = DoctorScheduleTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            DoctorLogModel.objects.create(
                user=user,
                doctor = serializer.instance,
                action='Create',
                description ='Doctor Schedule Created',
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        schedules = DoctorScheduleTemplate.objects.all()
        serializer = DoctorScheduleTemplateSerializer(schedules, many=True)
        return Response(serializer.data)

class DoctorScheduleTemplateEditView(APIView):


    permission_classes=[IsAuthenticated]


    def put(self, request, pk):
        user = request.user
        schedule = get_object_or_404(DoctorScheduleTemplate, pk=pk)
        serializer = DoctorScheduleTemplateSerializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DoctorScheduleExceptionView(APIView):


    permission_classes=[IsAuthenticated]



    def post(self, request):
        user = request.user
        serializer = DoctorScheduleExceptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            DoctorExceptionLogModel.objects.create(
                user=user,
                doctor = serializer.instance,
                action='create',
                description ='Doctor Schedule Exception Updated',
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        exceptions = DoctorScheduleException.objects.all()
        serializer = DoctorScheduleExceptionSerializer(exceptions, many=True)
        return Response(serializer.data)
    



class DoctorScheduleExceptionEditView(APIView):


    permission_classes=[IsAuthenticated]


    def patch(self, request, id=None):
        user=request.user
        if not id:
            return Response({"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            time_slot = DoctorExceptionTimeSlot.objects.get(id=id)
        except DoctorExceptionTimeSlot.DoesNotExist:
            return Response({"error": "No time slot found for the given ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorExceptionTimeSlotSerializer(time_slot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            doctor_schedule_exception = time_slot.exception_day
            DoctorExceptionLogModel.objects.create(
                user=user,
                doctor = doctor_schedule_exception,
                action='update',
                description ='Doctor Schedule Exception Updated',
                )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  



    def delete(self,request,id=None):
        user=request.user
        if not id:
            return Response({"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            time_slot = DoctorExceptionTimeSlot.objects.get(id=id)
        except DoctorExceptionTimeSlot.DoesNotExist:
            return Response({"error": "No time slot found for the given ID."}, status=status.HTTP_404_NOT_FOUND)
        time_slot.delete()
        doctor_schedule_exception = time_slot.exception_day
        DoctorExceptionLogModel.objects.create(
            user=user,
            doctor = doctor_schedule_exception,
            action='delete',    
            description ='Doctor Schedule Exception Deleted',
            )
        return Response({"message": "Doctor Schedule Exception deleted successfully"}, status=status.HTTP_200_OK)
    



class DoctorScheduleHolidayDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, date):
        try:
            with transaction.atomic():
                # Fetch the holiday exception for the given date
                exception = DoctorScheduleException.objects.get(date=date, is_holiday=True)

                # Log the deletion before actually deleting the exception
                DoctorExceptionLogModel.objects.create(
                    user=request.user,
                    doctor=exception,  # Ensure this is the correct related name
                    action='delete',
                    description=f'Holiday deleted for {date}'
                )

                # Now delete the exception
                exception.delete()

            return Response(
                {"message": "Holiday deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        except DoctorScheduleException.DoesNotExist:
            return Response(
                {"error": "No holiday found for this date"},
                status=status.HTTP_404_NOT_FOUND
            )
    


class DoctorTimeSlotDeleteView(APIView):

    # permission_classes = [IsAuthenticated]

    def delete(self, request, pk=None):
        user = request.user
        
        # Check if the time slot ID is provided
        if not pk:
            return Response(
                {"error": "Time slot ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fetch the time slot to be deleted
            time_slot = get_object_or_404(DoctorTimeSlot, id=pk)
            
            # Log the deletion action
            DoctorLogModel.objects.create(
                user=user,
                doctor=time_slot.schedule,  # Associate with the schedule template
                action='delete',
                description=f'Time slot deleted - Start Time: {time_slot.startTime}, End Time: {time_slot.endTime}'
            )
            
            # Delete the time slot
            time_slot.delete()
            
            return Response(
                {"message": "Time slot deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except DoctorTimeSlot.DoesNotExist:
            return Response(
                {"error": "Time slot not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"error": f"Failed to delete time slot: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#---------------------------------------------------Show Available Doctor Slots(All available)-------------------------------------------------


class AvailableDoctorSlotsView(APIView):


    permission_classes = [AllowAny]

    
    def get(self, request):
        # Get the date range
        start_date = datetime.strptime(
            request.query_params.get('start_date', datetime.now().date().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        ).date()
        
        # Get number of days to look ahead (default 7)
        days_ahead = int(request.query_params.get('days', 7))
        end_date = start_date + timedelta(days=days_ahead)

        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            # Get the weekday number (0 = Monday, 1 = Tuesday, etc.)
            weekday = current_date.weekday()
            
            # First check if there's an exception for this date
            try:
                exception = DoctorScheduleException.objects.get(date=current_date)
                if not exception.is_holiday:  # If not a holiday, use exception slots
                    for slot in exception.time_slots.all():
                        # Check if the slot is already booked for this specific date
                        existing_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime
                        )
                        if not existing_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': slot.isOnline,
                                'isOffline': slot.isOffline
                            })
            except DoctorScheduleException.DoesNotExist:
                # No exception found, use regular template
                day_schedule = DoctorScheduleTemplate.objects.filter(
                    day_of_week=weekday,
                    is_active=True
                ).first()

                if day_schedule:
                    for slot in day_schedule.time_slots.all():
                        # Check if the slot is already booked for this specific date
                        existing_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime
                        )
                        if not existing_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': slot.isOnline,
                                'isOffline': slot.isOffline
                            })

            current_date += timedelta(days=1)

            print(current_date)

        # Sort slots by date and start time
        available_slots.sort(key=lambda x: (x['date'], x['startTime']))
        
        return Response(available_slots, status=status.HTTP_200_OK)
    

#---------------------------------------------------Show Available Doctor Slots(Online)-------------------------------------------------

class AvailableOnlineSlotsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        start_date = datetime.strptime(
            request.query_params.get('start_date', datetime.now().date().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        ).date()
        days_ahead = int(request.query_params.get('days', 7))
        end_date = start_date + timedelta(days=days_ahead)
        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            weekday = current_date.weekday()

            # Check for exceptions first
            exceptions = DoctorScheduleException.objects.filter(date=current_date)  # Use filter() to get all exceptions for the date
            for exception in exceptions:  # Iterate over each exception
                if not exception.is_holiday:  # Check if the exception is not a holiday
                    for slot in exception.time_slots.filter(isOnline=True):  # Only online slots
                        # Check for conflicting bookings
                        conflicting_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime,
                            isOnline=True,
                            payment_status__in=["success", "on hold"]  # Only successful bookings block the slot
                        )
                        if not conflicting_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': True,
                                'isOffline': False
                            })

            # If no exceptions exist for the date, use the regular schedule
            if not exceptions.exists():
                day_schedule = DoctorScheduleTemplate.objects.filter(
                    day_of_week=weekday,
                    is_active=True
                ).first()
                if day_schedule:
                    for slot in day_schedule.time_slots.filter(isOnline=True):  # Only online slots
                        # Check for conflicting bookings
                        conflicting_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime,
                            isOnline=True,
                            payment_status__in=["success", "on hold"]  # Only successful bookings block the slot
                        )
                        if not conflicting_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': True,
                                'isOffline': False
                            })

            current_date += timedelta(days=1)

        # Sort the slots
        available_slots.sort(key=lambda x: (x['date'], x['startTime']))
        return Response(available_slots, status=status.HTTP_200_OK)


#---------------------------------------------------Show Available Doctor Slots(Offline)-------------------------------------------------

class AvailableOfflineSlotsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        start_date = datetime.strptime(
            request.query_params.get('start_date', datetime.now().date().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        ).date()
        days_ahead = int(request.query_params.get('days', 7))
        end_date = start_date + timedelta(days=days_ahead)
        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            weekday = current_date.weekday()

            # Check for exceptions first
            exceptions = DoctorScheduleException.objects.filter(date=current_date)  # Use filter() to get all exceptions for the date
            for exception in exceptions:  # Iterate over each exception
                if not exception.is_holiday:  # Check if the exception is not a holiday
                    for slot in exception.time_slots.filter(isOffline=True):  # Only offline slots
                        # Check for conflicting bookings
                        conflicting_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime,
                            isOffline=True,
                            payment_status__in=["success", "on hold"]  # Only successful bookings block the slot
                        )
                        if not conflicting_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': False,
                                'isOffline': True
                            })

            # If no exceptions exist for the date, use the regular schedule
            if not exceptions.exists():
                day_schedule = DoctorScheduleTemplate.objects.filter(
                    day_of_week=weekday,
                    is_active=True
                ).first()
                if day_schedule:
                    for slot in day_schedule.time_slots.filter(isOffline=True):  # Only offline slots
                        # Check for conflicting bookings
                        conflicting_bookings = UserSlot.objects.filter(
                            date=current_date,
                            startTime__lt=slot.endTime,
                            endTime__gt=slot.startTime,
                            isOffline=True,
                            payment_status__in=["success", "on hold"]  # Only successful bookings block the slot
                        )
                        if not conflicting_bookings.exists():
                            available_slots.append({
                                'date': current_date,
                                'startTime': slot.startTime,
                                'endTime': slot.endTime,
                                'isOnline': False,
                                'isOffline': True
                            })

            current_date += timedelta(days=1)

        # Sort the slots
        available_slots.sort(key=lambda x: (x['date'], x['startTime']))
        return Response(available_slots, status=status.HTTP_200_OK)
            
#---------------------------------------------------------------Razory pay Details----------------------------------------------------------------


class PaymentVerificationView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        # Get payment object
        payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
        user_slot = payment.user_slot
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            # Update payment and user slot status
            with transaction.atomic():
                payment.status = 'success'
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save()
                user_slot.payment_status = 'success'
                user_slot.save()
            # Handle meet link generation separately after payment is confirmed
            meet_link = None
            if user_slot.isOnline:
                try:
                    meet_link = self._generate_meet_link(user_slot)
                    user_slot.meet_link = meet_link
                    user_slot.save()
                except Exception as e:
                    if "Redirect to Google OAuth" in str(e):
                        return Response({
                            'message': 'Payment successful but OAuth authentication required',
                            'status': 'success',
                            'payment_status': 'success',
                            'meet_link_status': 'redirect',
                            'redirect_url': str(e).split(": ")[1]
                        }, status=status.HTTP_302_FOUND)
                    return Response({
                        'message': 'Payment successful but meet link generation failed',
                        'status': 'success',
                        'payment_status': 'success',
                        'meet_link_status': 'failed',
                        'meet_link_error': str(e)
                    }, status=status.HTTP_200_OK)
            return Response({
                'message': 'Payment verified successfully',
                'status': 'success',
                'meet_link': meet_link
            }, status=status.HTTP_200_OK)
        except razorpay.errors.SignatureVerificationError:
            # Handle payment verification failure
            with transaction.atomic():
                payment.status = 'failed'
                payment.save()
                user_slot.payment_status = 'failed'
                user_slot.save()
            return Response({
                'error': 'Payment verification failed',
                'status': 'failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    #Generating meet link

    def _generate_meet_link(self, user_slot):
        """
        Helper method to generate meet link for online meetings
        """
        meeting_data = {
            'firstName': user_slot.firstName,
            'lastName': user_slot.lastName,
            'email': user_slot.email,
            'isOnline': user_slot.isOnline,
            'isOffline': user_slot.isOffline,
            'startTime': user_slot.startTime,
            'endTime': user_slot.endTime,
            'date': user_slot.date,
            'message': user_slot.message,
            'meet_link': user_slot.meet_link,
            'created_at': user_slot.created_at,
            'payment_status': user_slot.payment_status,
        }
        try:
            return schedule_meeting(meeting_data)
        except Exception as e:
            if "Redirect to Google OAuth" in str(e):
                raise Exception(f"Redirect to Google OAuth: {str(e).split(': ')[1]}")
            raise e


class BookingConfirmationEmailView(APIView):

    permission_classes = [AllowAny]


    def post(self, request):
        try:
            slot_id = request.data.get('id')
            user_slot = get_object_or_404(UserSlot,id=slot_id)
            
            # Common email settings
            subject = "Booking Confirmation"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user_slot.email]
            
            # Prepare message based on booking type
            if user_slot.isOnline:
                message = f"""             
                <html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 30px auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
          
            text-align: center;
            padding: 20px;
        }}
        .header h1{{
            color: #026277;
            }}
        .header img {{
            max-width: 300px;
            height: auto;
           
        }}
        .important-notice {{
                    color: #666666;
                    font-weight: bold;
                    margin: 12px 0;
                    text-align: center;
                
                }}
                 .important-notice2 {{
                    color: #666666;
                    
                    margin: 12px 0;
                    text-align: center;
                
                }}
        .header h1 {{
            margin: 10px 0 0;
            font-size: 24px;
            font-weight: 300;
            color: white
        }}
        .content {{
            padding: 30px;
            background-color: #ffffff;
            border-top: 4px solid #026277;

        }}
        .details {{
           background-color: #f9f9f9;
            border-left: 4px solid #026277;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .details p {{
            margin: 10px 0;
            color: black;
        }}
        .details strong {{
            color: #027378;
            min-width: 100px;
            display: inline-block;
        }}
        .system-notice {{
                    font-family: 'Courier New', monospace;
                    color: #666;
                    font-size: 0.9em;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }}
        .meeting-link {{
            display: block;
            text-align: center;
            margin: 20px 0;
        }}
        .meeting-link a {{
            background-color: #027378;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }}
        .meeting-link a:hover {{
            background-color: #027378;
        }}
        .footer {{
            background-color: #f4f4f4;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
            color: #777;
        }}
        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://metabolicresetwithbob.com/assets/Logo-DFOA3T0r.png" alt="Metabolic Reset With Bob">
            <h1>Consultation Confirmation</h1>
        </div>
        <div class="content">
            <p>Dear {user_slot.firstName},</p>
            <p>Your online consultation slot has been successfully booked. Please find the details below:</p>
            
            <div class="details">
                <p><strong>Date:</strong> {user_slot.date.strftime('%Y-%m-%d')}</p>
                <p><strong>Time:</strong> {user_slot.startTime.strftime('%I:%M %p')} - {user_slot.endTime.strftime('%I:%M %p')}</p>
            </div>
            
            <div class="meeting-link">
                <a href="{user_slot.meet_link}">Join Video Consultation</a>
            </div>
            
            <p class="important-notice2">Please ensure you have a stable internet connection and are in a quiet environment for your consultation. If you need to reschedule, please contact our office at least 24 hours in advance.</p>
        <p class="important-notice">Note: The consultation fee is non-refundable but can be rescheduled.</p>
         </div>
        <div class="footer">
            <p>Best regards,</p>
            <p><strong>Bob Chris</strong></p>
            <p>Metabolic Reset With Bob</p>

            <div class="system-notice">
                This is a system-generated email. Please do not reply to this message.
            </div>

        </div>
    </div>
</body>
</html>
                """
            
            else:
                message = f"""
               <html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
         .important-notice {{
                    color: #666666;
                    font-weight: bold;
                    margin: 12px 0;
                    text-align: center;
                
                }}
                 .important-notice2 {{
                    color: #666666;
                    
                    margin: 12px 0;
                    text-align: center;
                
                }}
        .container {{
            max-width: 600px;
            margin: 30px auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .system-notice {{
                    font-family: 'Courier New', monospace;
                    color: #666;
                    font-size: 0.9em;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }}
        .header {{
            text-align: center;
            padding: 20px;
        }}

        .header h1{{
                    color: #026277;
                }}

        .header img {{
            max-width: 300px;
            height: auto;
           
        }}
        .content {{
            padding: 30px;
            background-color: #ffffff;
            border-top: 4px solid #026277;
        }}
        .details {{
            background-color: #f9f9f9;
            border-left: 4px solid #026277;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .details p {{
            margin: 10px 0;
            color:black;
        }}
        .details strong {{
            color: #027378;
            min-width: 100px;
            display: inline-block;
        }}
        .clinic-info {{
            background-color: #e8f5e9;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            text-align: center;
        }}
        .footer {{
            background-color: #f4f4f4;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
            color: #777;
        }}
        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://metabolicresetwithbob.com/assets/Logo-DFOA3T0r.png" alt="Metabolic Reset With Bob">
            <h1>Consultation Confirmation</h1>
        </div>
        <div class="content">
            <p>Dear {user_slot.firstName},</p>
            <p>Your in-person consultation slot has been successfully booked.</p>
            
            <div class="details">
                <p><strong>Date:</strong> {user_slot.date.strftime('%Y-%m-%d')}</p>
                <p><strong>Time:</strong> {user_slot.startTime.strftime('%I:%M %p')} - {user_slot.endTime.strftime('%I:%M %p')}</p>
            </div>
            
            <div class="clinic-info">
                <p>Please arrive at our clinic 10 minutes before your scheduled time.</p>
                <p><strong>Clinic Address:</strong> H.NO.1920, Sector 34-D, (Near Radio Station)
              Chandigarh - 160034, INDIA</p>
            </div>
            
            <p class="important-notice2">We look forward to providing you with personalized homeopathic care.</p>
            <p class="important-notice">Note: The consultation fee is non-refundable but can be rescheduled.</p>
        </div>
        <div class="footer">
            <p>Best regards,</p>
            <p><strong>Bob Chris</strong></p>
            <p>Metabolic Reset With Bob</p>
             <div class="system-notice">
                This is a system-generated email. Please do not reply to this message.
            </div>

        </div>
    </div>
</body>
</html>
                """
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
                html_message=message,  # This ensures the email is sent as HTML
            )

            
            return Response({
                "message": "Booking confirmation email sent successfully"
            }, status=status.HTTP_200_OK)
            
        except UserSlot.DoesNotExist:
            return Response({
                "message": "Booking not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": "An error occurred while processing your request",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class OAuth2CallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            state = request.GET.get('state')
            cached_state = cache.get('oauth_state')
            if not state or state != cached_state:
                return HttpResponse("Invalid state parameter", status=400)

            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(settings.BASE_DIR, 'credentials.json'),
                scopes=['https://www.googleapis.com/auth/calendar.events'],
                redirect_uri='https://metabolicresetwithbob.com/oauth2callback'
            )
            flow.fetch_token(code=request.GET.get('code'))
            credentials = flow.credentials

            # Save credentials to database
            token_data = json.loads(credentials.to_json())
            GoogleToken.objects.update_or_create(
                id=1,
                defaults={
                    'token': token_data['token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'token_uri': token_data['token_uri'],
                    'client_id': token_data['client_id'],
                    'client_secret': token_data['client_secret'],
                    'scopes': token_data['scopes'],
                    'expiry': datetime.datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00')),
                }
            )

            # Clear cached state
            cache.delete('oauth_state')

            # Redirect to a success page or frontend
            return HttpResponseRedirect('https://metabolicresetwithbob.com/booking-success')  # Adjust to your frontend success URL
        except Exception as e:
            return HttpResponse(f"Error in OAuth callback: {str(e)}", status=500)






class ProductFeesCreateView(APIView):
    """
    Create a new Product with multiple images and link it to a FeesModel entry.
    Similar to FeesCreateView but for Product instead of Program.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Extract fee amounts
        amount_online = request.data.get('amountOnline')
        amount_offline = request.data.get('amountOffline')  # Optional, like in your model

        if not amount_online:
            return Response(
                {"error": "amountOnline is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount_online = int(amount_online)
            amount_offline = int(amount_offline) if amount_offline is not None else None
        except (TypeError, ValueError):
            return Response(
                {"error": "amountOnline and amountOffline must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Required Product fields (title is required as per your model)
        title = request.data.get('title', '').strip()
        alt_text = request.data.get('alt_text', '').strip()

        if not title:
            return Response(
                {"error": "title is required for Product."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cover image is required in your Product model
        cover_image_file = request.FILES.get('cover_image')
        if not cover_image_file:
            return Response(
                {"error": "cover_image is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not cover_image_file.content_type.startswith('image/'):
            return Response(
                {"error": "cover_image must be a valid image file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        pdf_file = request.FILES.get('pdf')  # Client should send under key "pdf"
        if pdf_file:
            if not pdf_file.content_type == 'application/pdf':
                return Response(
                    {"error": f"File {pdf_file.name} is not a valid PDF."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create the Product
        product = Product.objects.create(
            title=title,
            alt_text=alt_text,
            cover_image=cover_image_file,
            pdf=pdf_file
        )

        # Handle additional images (ManyToMany)
        files = request.FILES.getlist('image')  # Multiple files with key "image"
        if not files:
            # Fallback for image[0], image[1], etc.
            i = 0
            while True:
                file_key = f'image[{i}]'
                file = request.FILES.get(file_key)
                if not file:
                    break
                files.append(file)
                i += 1

        uploaded_images = []
        for image_file in files:
            if not image_file.content_type.startswith('image/'):
                return Response(
                    {"error": f"File {image_file.name} is not a valid image."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product_image = ProductImage.objects.create(image=image_file)
            uploaded_images.append(product_image)

        if uploaded_images:
            product.images.add(*uploaded_images)

        # Create the Fees entry linked to this Product
        fees = FeesModel.objects.create(
            amountOnline=amount_online,
            amountOffline=amount_offline,
            product=product
        )

        # Build response
        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat(),
            "product": {
                "id": product.id,
                "title": product.title,
                "alt_text": product.alt_text,
                "cover_image": request.build_absolute_uri(product.cover_image.url),
                "pdf": request.build_absolute_uri(product.pdf.url) if product.pdf else None,
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                        "alt_text": img.alt_text or "",
                        "uploaded_at": img.uploaded_at.isoformat()
                    }
                    for img in product.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    

class ProductFeesList(APIView):
    """
    List all Products that have associated Fees, along with their fees and images.
    Queried Product-wise (starting from Product model via reverse relation).
    Response structure remains the same as before.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Start from Product model, only include those that have at least one Fees entry
        # Use prefetch_related to efficiently get the related FeesModel (reverse FK)
        # Since FeesModel has ForeignKey to Product (related_name='product'), reverse is 'feesmodel_set'
        # But to be safe and explicit, we'll filter products that have fees

        products_with_fees = Product.objects.filter(product__isnull=False).distinct() \
            .prefetch_related(
                Prefetch(
                    'product',  # This is the reverse relation: FeesModel objects linked to this Product
                    queryset=FeesModel.objects.order_by('-created_at')  # Optional: latest fees first
                )
            ) \
            .prefetch_related('images') \
            .order_by('-product__created_at')  # Order by most recent fee creation

        data = []

        for product in products_with_fees:
            # Get the most recent (or only) fees entry linked to this product
            # Since a Product should typically have only one Fees entry, take the first
            fees = product.product.first()  # reverse relation

            if not fees:
                continue  # Skip if somehow no fees (shouldn't happen due to filter)

            entry = {
                "fees_id": fees.id,
                "amountOnline": fees.amountOnline,
                "amountOffline": fees.amountOffline,
                "created_at": fees.created_at.isoformat() if fees.created_at else None,
                "updated_at": fees.updated_at.isoformat() if fees.updated_at else None,
                "product": {
                    "id": product.id,
                    "title": product.title,
                    "alt_text": product.alt_text,
                    "cover_image": request.build_absolute_uri(product.cover_image.url),
                    "pdf": request.build_absolute_uri(product.pdf.url) if product.pdf else None,
                    "images": [
                        {
                            "id": img.id,
                            "url": request.build_absolute_uri(img.image.url),
                            "alt_text": img.alt_text or "",
                            "uploaded_at": img.uploaded_at.isoformat()
                        }
                        for img in product.images.all()
                    ]
                }
            }

            data.append(entry)

        return Response(data, status=status.HTTP_200_OK)



class ProductFeesDetailView(APIView):
    """
    Retrieve, update or delete a Product along with its linked FeesModel entry.
    Now operates Product-wise: endpoint uses Product ID (pk).
    Response structure remains identical to previous version.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # pk is now the Product ID
        product = get_object_or_404(Product, pk=pk)

        # Get the associated Fees (reverse relation via related_name='product')
        fees = getattr(product, 'product', None)  # product.product gives the FeesModel instance(s)

        if not fees:
            return Response(
                {"error": "This Product has no associated fees."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Since it's one-to-one in practice, take the first (and only) fees
        fees = fees.first()

        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat() if fees.created_at else None,
            "updated_at": fees.updated_at.isoformat() if fees.updated_at else None,
            "pdf": request.build_absolute_uri(product.pdf.url) if product.pdf else None,
            "product": {
                "id": product.id,
                "title": product.title,
                "alt_text": product.alt_text,
                "cover_image": request.build_absolute_uri(product.cover_image.url),
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                        "alt_text": img.alt_text or "",
                        "uploaded_at": img.uploaded_at.isoformat()
                    }
                    for img in product.images.all()
                ]
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        # pk is now Product ID
        product = get_object_or_404(Product, pk=pk)

        fees = getattr(product, 'product', None)
        if not fees:
            return Response(
                {"error": "This Product has no associated fees to update."},
                status=status.HTTP_404_NOT_FOUND
            )
        fees = fees.first()

        # Update fee amounts
        amount_online = request.data.get('amountOnline')
        amount_offline = request.data.get('amountOffline')

        if amount_online is None and amount_offline is None:
            return Response(
                {"error": "At least one of amountOnline or amountOffline is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount_online is not None:
            try:
                fees.amountOnline = int(amount_online)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOnline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if amount_offline is not None:
            try:
                fees.amountOffline = int(amount_offline)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOffline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        fees.save()

        # Update product fields
        title = request.data.get('title')
        alt_text = request.data.get('alt_text')

        if title is not None:
            title = title.strip()
            if not title:
                return Response({"error": "title cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            product.title = title

        if alt_text is not None:
            product.alt_text = alt_text.strip()

        # Optional: Replace cover image
        cover_image_file = request.FILES.get('cover_image')
        if cover_image_file:
            if not cover_image_file.content_type.startswith('image/'):
                return Response(
                    {"error": "New cover_image must be a valid image file."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if product.cover_image:
                product.cover_image.delete(save=False)
            product.cover_image = cover_image_file

        pdf_file = request.FILES.get('pdf')
        if pdf_file:
            if pdf_file.content_type != 'application/pdf':
                return Response(
                    {"error": f"File {pdf_file.name} is not a valid PDF."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if product.pdf:
                product.pdf.delete(save=False)  # Delete old PDF file
            product.pdf = pdf_file

        # Optional: Remove PDF entirely
        remove_pdf = request.data.get('remove_pdf')
        if remove_pdf in ('true', '1', True):
            if product.pdf:
                product.pdf.delete(save=False)
                product.pdf = None

        product.save()


        # Handle removal of additional images
        remove_images_str = request.data.get('remove_images')
        if remove_images_str:
            try:
                remove_ids = json.loads(remove_images_str)
                if not isinstance(remove_ids, list):
                    raise ValueError
                images_to_remove = ProductImage.objects.filter(id__in=remove_ids, product=product)
                for img in images_to_remove:
                    img.image.delete(save=False)
                    img.delete()
                product.images.remove(*images_to_remove)
            except (json.JSONDecodeError, ValueError):
                return Response(
                    {"error": "remove_images must be a valid JSON list of image IDs."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Add new additional images
        files = request.FILES.getlist('image')
        if not files:
            i = 0
            while True:
                file_key = f'image[{i}]'
                file = request.FILES.get(file_key)
                if not file:
                    break
                files.append(file)
                i += 1

        uploaded_images = []
        for image_file in files:
            if not image_file.content_type.startswith('image/'):
                return Response(
                    {"error": f"File {image_file.name} is not a valid image."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product_image = ProductImage.objects.create(image=image_file)
            uploaded_images.append(product_image)

        if uploaded_images:
            product.images.add(*uploaded_images)

        # Build updated response (same structure)
        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat(),
            "updated_at": fees.updated_at.isoformat(),
            "product": {
                "id": product.id,
                "title": product.title,
                "alt_text": product.alt_text,
                "cover_image": request.build_absolute_uri(product.cover_image.url),
                "pdf": request.build_absolute_uri(product.pdf.url) if product.pdf else None,
                
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                    }
                    for img in product.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        # pk is now Product ID
        product = get_object_or_404(Product, pk=pk)

        fees = getattr(product, 'product', None)
        if not fees:
            return Response(
                {"error": "This Product has no associated fees to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

        fees = fees.first()
        fees.delete()

        return Response(
            {"message": "Product fees deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

class ProductListFrontend(APIView):
    """
    List all Products that have associated Fees, along with their fees and images.
    Queried Product-wise (starting from Product model via reverse relation).
    Response structure remains the same as before.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Start from Product model, only include those that have at least one Fees entry
        # Use prefetch_related to efficiently get the related FeesModel (reverse FK)
        # Since FeesModel has ForeignKey to Product (related_name='product'), reverse is 'feesmodel_set'
        # But to be safe and explicit, we'll filter products that have fees

        products_with_fees = Product.objects.filter(product__isnull=False).distinct() \
            .prefetch_related(
                Prefetch(
                    'product',  # This is the reverse relation: FeesModel objects linked to this Product
                    queryset=FeesModel.objects.order_by('-created_at')  # Optional: latest fees first
                )
            ) \
            .prefetch_related('images') \
            .order_by('-product__created_at')  # Order by most recent fee creation

        data = []

        for product in products_with_fees:
            # Get the most recent (or only) fees entry linked to this product
            # Since a Product should typically have only one Fees entry, take the first
            fees = product.product.first()  # reverse relation

            if not fees:
                continue  # Skip if somehow no fees (shouldn't happen due to filter)

            entry = {
                "fees_id": fees.id,
                "amountOnline": fees.amountOnline,
                "amountOffline": fees.amountOffline,
                "created_at": fees.created_at.isoformat() if fees.created_at else None,
                "updated_at": fees.updated_at.isoformat() if fees.updated_at else None,
                "product": {
                    "id": product.id,
                    "title": product.title,
                    "alt_text": product.alt_text,
                    "cover_image": request.build_absolute_uri(product.cover_image.url),
                    "images": [
                        {
                            "id": img.id,
                            "url": request.build_absolute_uri(img.image.url),
                            "alt_text": img.alt_text or "",
                            "uploaded_at": img.uploaded_at.isoformat()
                        }
                        for img in product.images.all()
                    ]
                }
            }

            data.append(entry)

        return Response(data, status=status.HTTP_200_OK)




class ProductDetailFrontend(APIView):
    """
    Retrieve, update or delete a Product along with its linked FeesModel entry.
    Now operates Product-wise: endpoint uses Product ID (pk).
    Response structure remains identical to previous version.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        # pk is now the Product ID
        product = get_object_or_404(Product, pk=pk)

        # Get the associated Fees (reverse relation via related_name='product')
        fees = getattr(product, 'product', None)  # product.product gives the FeesModel instance(s)

        if not fees:
            return Response(
                {"error": "This Product has no associated fees."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Since it's one-to-one in practice, take the first (and only) fees
        fees = fees.first()

        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat() if fees.created_at else None,
            "updated_at": fees.updated_at.isoformat() if fees.updated_at else None,
            "product": {
                "id": product.id,
                "title": product.title,
                "alt_text": product.alt_text,
                "cover_image": request.build_absolute_uri(product.cover_image.url),
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                        "alt_text": img.alt_text or "",
                        "uploaded_at": img.uploaded_at.isoformat()
                    }
                    for img in product.images.all()
                ]
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        # pk is now Product ID
        product = get_object_or_404(Product, pk=pk)

        fees = getattr(product, 'product', None)
        if not fees:
            return Response(
                {"error": "This Product has no associated fees to update."},
                status=status.HTTP_404_NOT_FOUND
            )
        fees = fees.first()

        # Update fee amounts
        amount_online = request.data.get('amountOnline')
        amount_offline = request.data.get('amountOffline')

        if amount_online is None and amount_offline is None:
            return Response(
                {"error": "At least one of amountOnline or amountOffline is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount_online is not None:
            try:
                fees.amountOnline = int(amount_online)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOnline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if amount_offline is not None:
            try:
                fees.amountOffline = int(amount_offline)
            except (TypeError, ValueError):
                return Response(
                    {"error": "amountOffline must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        fees.save()

        # Update product fields
        title = request.data.get('title')
        alt_text = request.data.get('alt_text')

        if title is not None:
            title = title.strip()
            if not title:
                return Response({"error": "title cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            product.title = title

        if alt_text is not None:
            product.alt_text = alt_text.strip()

        # Optional: Replace cover image
        cover_image_file = request.FILES.get('cover_image')
        if cover_image_file:
            if not cover_image_file.content_type.startswith('image/'):
                return Response(
                    {"error": "New cover_image must be a valid image file."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if product.cover_image:
                product.cover_image.delete(save=False)
            product.cover_image = cover_image_file

        product.save()

        # Handle removal of additional images
        remove_images_str = request.data.get('remove_images')
        if remove_images_str:
            try:
                remove_ids = json.loads(remove_images_str)
                if not isinstance(remove_ids, list):
                    raise ValueError
                images_to_remove = ProductImage.objects.filter(id__in=remove_ids, product=product)
                for img in images_to_remove:
                    img.image.delete(save=False)
                    img.delete()
                product.images.remove(*images_to_remove)
            except (json.JSONDecodeError, ValueError):
                return Response(
                    {"error": "remove_images must be a valid JSON list of image IDs."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Add new additional images
        files = request.FILES.getlist('image')
        if not files:
            i = 0
            while True:
                file_key = f'image[{i}]'
                file = request.FILES.get(file_key)
                if not file:
                    break
                files.append(file)
                i += 1

        uploaded_images = []
        for image_file in files:
            if not image_file.content_type.startswith('image/'):
                return Response(
                    {"error": f"File {image_file.name} is not a valid image."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product_image = ProductImage.objects.create(image=image_file)
            uploaded_images.append(product_image)

        if uploaded_images:
            product.images.add(*uploaded_images)

        # Build updated response (same structure)
        response_data = {
            "fees_id": fees.id,
            "amountOnline": fees.amountOnline,
            "amountOffline": fees.amountOffline,
            "created_at": fees.created_at.isoformat(),
            "updated_at": fees.updated_at.isoformat(),
            "product": {
                "id": product.id,
                "title": product.title,
                "alt_text": product.alt_text,
                "cover_image": request.build_absolute_uri(product.cover_image.url),
                "images": [
                    {
                        "id": img.id,
                        "url": request.build_absolute_uri(img.image.url),
                    }
                    for img in product.images.all()
                ]
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        # pk is now Product ID
        product = get_object_or_404(Product, pk=pk)

        fees = getattr(product, 'product', None)
        if not fees:
            return Response(
                {"error": "This Product has no associated fees to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

        fees = fees.first()
        fees.delete()

        return Response(
            {"message": "Product fees deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
    



class ProductHistory(APIView):
    def post(self,request):
        fees_id = request.data.get('fees_id')
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        address = request.data.get('address')
        product_id = request.data.get('product_id')


        with transaction.atomic():
            try:
            
                try:
                    fee_config = FeesModel.objects.get(id=fees_id)
                except FeesModel.DoesNotExist:
                    return Response({"error": "Invalid fees_id: Fee configuration not found"}, status=status.HTTP_400_BAD_REQUEST)
                
                product = get_object_or_404(Product,id=product_id)

                product_history_create = ProductBuyHistory.objects.create(
                    name = name,
                    email = email,
                    phone = phone,
                    address = address,
                    product=product
                )
                # Initialize Razorpay client
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                client.set_app_details({
                    "title": "Django",
                    "version": "5.1.4"
                })                
                
                # Set amount based on meeting type
                amount = fee_config.amountOnline

                print("####################################################################################",amount)
                
                # Create Razorpay order
                razorpay_order = client.order.create({
                    'amount': int(amount * 100),  # Amount in paise
                    'currency': 'INR',
                    'payment_capture': 1,
                    'notes': {
                        'product__buy_history_id': product_history_create.id,
                        'name': f"{product_history_create.name}",
                        'email': product_history_create.email,
                        'phone': product_history_create.phone,
                        'product_id':product_history_create.product.id,
                        'product_name':product_history_create.product.title
                    }
                })


                
                # Create payment record
                payment = Payment.objects.create(
                    product_history=product_history_create,
                    razorpay_order_id=razorpay_order['id'],
                    amount=amount
                )
                
                return Response({
                    'product_id': product_history_create.id,
                    'name': f"{product_history_create.name}",
                    'email': product_history_create.email,
                    'phone': product_history_create.phone,
                    'payment': {
                        'order_id': razorpay_order['id'],
                        'amount': amount,
                        'currency': 'INR'
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # The transaction will automatically roll back in case of any exception
                return Response(
                    {"error": f"Failed to process request: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )





class PaymentVerificationViewProduct(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        # Get payment object
        payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
        product_history = payment.product_history
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            # Update payment and user slot status
            with transaction.atomic():
                payment.status = 'success'
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save()
                product_history.payment_status = 'success'
                product_history.is_sold=True
                product_history.save()
            # Handle meet link generation separately after payment is confirmed
            
            return Response({
                'message': 'Payment of Product verified successfully',
                'status': 'success',
            }, status=status.HTTP_200_OK)
        except razorpay.errors.SignatureVerificationError:
            # Handle payment verification failure
            with transaction.atomic():
                payment.status = 'failed'
                payment.save()
                product_history.payment_status = 'failed'
                product_history.save()
            return Response({
                'error': 'Payment verification failed',
                'status': 'failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class BookingConfirmationProduct(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            product_history_id = request.data.get('id')
            product_buy_history = get_object_or_404(ProductBuyHistory, id=product_history_id)

            # Check if a product is associated (and has a PDF)
            if not product_buy_history.product or not product_buy_history.product.pdf:
                return Response({
                    "message": "No PDF available for this purchase"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Common email settings
            subject = "Your Purchase Confirmation & Download"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [product_buy_history.email]

            # Updated HTML message for product purchase (no consultation/zoom link)
            message = f"""
            <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
                    
                    body {{
                        font-family: 'Roboto', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 30px auto;
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        text-align: center;
                        padding: 20px;
                    }}
                    .header h1 {{
                        color: #026277;
                    }}
                    .header img {{
                        max-width: 300px;
                        height: auto;
                    }}
                    .important-notice {{
                        color: #666666;
                        font-weight: bold;
                        margin: 12px 0;
                        text-align: center;
                    }}
                    .important-notice2 {{
                        color: #666666;
                        margin: 12px 0;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 10px 0 0;
                        font-size: 24px;
                        font-weight: 300;
                        color: white;
                    }}
                    .content {{
                        padding: 30px;
                        background-color: #ffffff;
                        border-top: 4px solid #026277;
                    }}
                    .details {{
                        background-color: #f9f9f9;
                        border-left: 4px solid #026277;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 0 8px 8px 0;
                    }}
                    .details p {{
                        margin: 10px 0;
                        color: black;
                    }}
                    .details strong {{
                        color: #027378;
                        min-width: 100px;
                        display: inline-block;
                    }}
                    .system-notice {{
                        font-family: 'Courier New', monospace;
                        color: #666;
                        font-size: 0.9em;
                        text-align: center;
                        margin: 20px 0;
                        padding: 10px;
                        background-color: #f5f5f5;
                        border-radius: 5px;
                    }}
                    .footer {{
                        background-color: #f4f4f4;
                        text-align: center;
                        padding: 20px;
                        font-size: 0.9em;
                        color: #777;
                    }}
                    .footer p {{
                        margin: 5px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <img src="https://metabolicresetwithbob.com/assets/Logo-DFOA3T0r.png" alt="Metabolic Reset With Bob">
                        <h1>Purchase Confirmation</h1>
                    </div>
                    <div class="content">
                        <p>Dear {product_buy_history.name},</p>
                        <p>Thank you for your purchase! Your order has been successfully processed.</p>
                        <p><strong>Product:</strong> {product_buy_history.product.title}</p>
                        
                        <p>Your downloadable PDF is attached to this email for your convenience.</p>
                        
                        <p class="important-notice2">If you have any questions or need support, feel free to reply to this email.</p>
                        <p class="important-notice">Note: This purchase is non-refundable.</p>
                    </div>
                    <div class="footer">
                        <p>Best regards,</p>
                        <p><strong>Bob Chris</strong></p>
                        <p>Metabolic Reset With Bob</p>

                        <div class="system-notice">
                            This is a system-generated email. Please do not reply to this message.
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            # Use EmailMessage to support attachments and HTML
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
            )
            email.content_subtype = "html"  # Ensures the body is treated as HTML

            # Attach the PDF from the related Product
            pdf_file = product_buy_history.product.pdf
            pdf_file.open('rb')  # Open the file in binary mode
            email.attach(
                filename=pdf_file.name.split('/')[-1],  # Use original filename
                content=pdf_file.read(),
                mimetype='application/pdf'
            )
            pdf_file.close()

            # Send the email
            email.send(fail_silently=False)

            return Response({
                "message": "Purchase confirmation email with PDF attachment sent successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "An error occurred while processing your request",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class ProductPaymnetHistoryList(APIView):
    def get(self,request):
        product_history = ProductBuyHistory.objects.all().order_by('-created_at')

        product_history_data = []


        for history in product_history:
            product_history_data.append({
                'name':history.name,
                'email':history.email,
                'phone':history.phone,
                'address':history.address,
                'payment_status':history.payment_status,
                'product_details':[{
                    'product_id':history.product.id,
                    'title':history.product.title,
                    'amount':[{
                        'amount':amount.amountOnline
                    }for amount in FeesModel.objects.filter(product=history.product)]
                }]
            })

        return Response(history,status=status.HTTP_200_OK)