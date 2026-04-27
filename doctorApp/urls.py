from django.urls import path


from .views import *
from . import views

from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [

#-----------------------------------------------------------Fess Create---------------------------------------------------------------------------

    path('fees/create/',FeesCreateView.as_view(),name='fees'),

    path('fees/int:pk>/',FeesDetailView.as_view(),name='fees-delete'),

    path('fees/delete/int:pk>/',FeesDelete.as_view(),name='fees-delete-new'),





#---------------------------------------------------------Fees List--------------------------------------------------------------------

    path('fees/show/',FeesShowView.as_view(),name='fees-list'),


#---------------------------------------------------------Fees List--------------------------------------------------------------------

    path('fees/show/backend/',FeesShowBackendView.as_view(),name='fees-list'),


#---------------------------------------------------------Fees List All--------------------------------------------------------------------

    path('fees/show/all/',FeesShowAllView.as_view(),name='fees-list'),


#------------------------------------------------------Adding User Slot-------------------------------------------------

    path('user_AddSlot/',UserSlotView.as_view(),name='user_slotAdd'),


    path('user_UpdateSlot/<int:pk>/',UserSlotView.as_view(),name='user_slotUpdate'),
    
    path('user_DeleteSlot/<int:pk>/',UserSlotView.as_view(),name='user_slotDelete'),



#------------------------------------------------------Adding User Frontend Slot-------------------------------------------------

    path('user_AddSlot/frontend/',UserSlotFrontendView.as_view(),name='user_slotAdd'),



#------------------------------------------------------Showing User Slot-------------------------------------------------

    path('user_Show/',UserShowView.as_view(),name='user-show'),


#----------------------------------------------Showing User Slot by filtering with the name-------------------------------------------------

    path('user_Show_Filter/',UserShow_filterView.as_view(),name='user-show-filter'),

   
#------------------------------------------------------Adding Doctor Slot-------------------------------------------------

    path('doctor/schedule-template/', DoctorScheduleTemplateView.as_view(), name='doctor-slots-list'),


#------------------------------------------------------Editing Doctor Slot-------------------------------------------------

    path('doctor/schedule-template/edit/',DoctorScheduleTemplateEditView.as_view(),name='doctor-schedule-template-edit'),


#------------------------------------------------------Add Exception Slot-------------------------------------------------

    path('doctor/schedule-exception/', DoctorScheduleExceptionView.as_view(), name='doctor-slots-detail'),


#-----------------------------------------------------Edit the doctor Schedule exception--------------------------------------------------

    path('doctor/schedule-exception-edit/<int:id>/', DoctorScheduleExceptionEditView.as_view(), name='doctor-schedule-exception-edit'),
    

#------------------------------------------------------Checking Available Slot-------------------------------------------------------------

    path('doctor/available-slots/',AvailableDoctorSlotsView.as_view(),name='availableSlot'),    


#--------------------------------------------------Checking Available Online Slot-------------------------------------------------------------

    path('availableOnline/',AvailableOnlineSlotsView.as_view(),name='available-online'),


#--------------------------------------------------Checking Available Offline Slot-------------------------------------------------------------

    path('availableOffline/',AvailableOfflineSlotsView.as_view(),name='available-offline'),


#------------------------------------------------------Paayment Verification-------------------------------------------------

    path('verify/',PaymentVerificationView.as_view(),name='Payment-verification'),


#------------------------------------------------------Booking Confirmation-------------------------------------------------

    path('booking-confirmation/', BookingConfirmationEmailView.as_view(), name='booking-confirmation'),



    path('doctor/time-slots/delete/<int:pk>/', DoctorTimeSlotDeleteView.as_view(), name='doctor-time-slot-delete'),


    path('oauth2callback/', views.OAuth2CallbackView.as_view(), name='oauth2callback'),




    path('product-fees/create/', ProductFeesCreateView.as_view(), name='product-fees-create'),

    path('product-fees/', ProductFeesList.as_view(), name='product-fees'),


    path('product-fees/<int:pk>/', ProductFeesDetailView.as_view(), name='product-fees-detail'),


    path('product-list/frontend/', ProductListFrontend.as_view(), name='product-list-frotnend'),

    path('product-detail/frontend/<int:pk>/', ProductDetailFrontend.as_view(), name='product-detail-frotnend'),






    path('product-payment-history-create/', ProductHistory.as_view(), name='product-history'),



    path('product/paymnet/verify/',PaymentVerificationViewProduct.as_view(),name='Payment-verification-product'),

    path('product-booking-confirmation/', BookingConfirmationProduct.as_view(), name='product-booking-confirmation'),


    path('product-payment-history-list/', ProductPaymnetHistoryList.as_view(), name='product-history-list'),


]