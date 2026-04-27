import os
import datetime
import json
import logging
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.cache import cache
from doctorApp.models import GoogleToken

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, 'credentials.json')

class GoogleCalendarService:
    def __init__(self):
        logger.info("Initializing GoogleCalendarService...")
        self.credentials = self._get_credentials()
        logger.info("Credentials successfully loaded or created.")
        self.service = build('calendar', 'v3', credentials=self.credentials)

    def _get_credentials(self) -> Credentials:
        """
        Get or refresh Google Calendar API credentials with automatic token refresh.
        Returns:
            Credentials: Valid Google Calendar API credentials
        Raises:
            Exception: If OAuth authentication is required
        """
        creds = None
        logger.info("Checking for existing token in database...")

        # Try to load token from database
        token_obj = GoogleToken.objects.first()  # Assuming one token for simplicity
        if token_obj:
            try:
                logger.info("Token found in database. Loading token...")
                token_data = {
                    'token': token_obj.token,
                    'refresh_token': token_obj.refresh_token,
                    'token_uri': token_obj.token_uri,
                    'client_id': token_obj.client_id,
                    'client_secret': token_obj.client_secret,
                    'scopes': token_obj.scopes,
                    'expiry': token_obj.expiry.isoformat(),
                }
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                
                # Check if token is expired or invalid
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        logger.info("Token expired. Attempting to refresh...")
                        try:
                            creds.refresh(Request())
                            logger.info("Token refreshed successfully.")
                            self._save_credentials(creds)  # Save refreshed token
                        except RefreshError as e:
                            logger.error(f"Failed to refresh token: {str(e)}", exc_info=True)
                            creds = None  # Force re-authentication
                    else:
                        logger.warning("Token is invalid and no refresh token available.")
                        creds = None
                else:
                    logger.info("Token is valid.")
            except Exception as e:
                logger.error(f"Error loading credentials: {str(e)}", exc_info=True)
                creds = None
        else:
            logger.info("No existing token found in database.")

        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            try:
                logger.info("Initiating new OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH,
                    SCOPES,
                    redirect_uri='https://metabolicresetwithbob.com/oauth2callback'
                )
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                cache.set('oauth_state', flow.state, timeout=3600)
                logger.info(f"OAuth flow initiated. Redirect URL: {auth_url}")
                raise Exception(f"Redirect to Google OAuth: {auth_url}")
            except Exception as e:
                if "Redirect to Google OAuth" in str(e):
                    raise  # Re-raise OAuth redirect exception
                logger.error(f"Failed to initiate OAuth flow: {str(e)}", exc_info=True)
                raise Exception(f"Failed to initiate OAuth flow: {str(e)}")

        return creds

    def _save_credentials(self, creds: Credentials) -> None:
        """
        Save credentials to database with error handling.
        Args:
            creds: Credentials object to save
        """
        try:
            token_data = json.loads(creds.to_json())
            if not token_data.get('refresh_token'):
                logger.warning("No refresh token present in credentials.")
            GoogleToken.objects.update_or_create(
                id=1,  # Assuming one token for simplicity
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
            logger.info("Credentials saved successfully to database.")
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}", exc_info=True)
            raise Exception(f"Failed to save credentials: {str(e)}")

    def create_event_body(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the event body for Google Calendar API.
        Args:
            meeting_data: Dictionary containing meeting details
        Returns:
            Dict containing the formatted event data
        """
        logger.info(f"Creating event body for meeting with {meeting_data['firstName']} {meeting_data['lastName']}...")
        
        # Combine date and time objects to create datetime objects
        meeting_date = meeting_data['date']
        start_time = meeting_data['startTime']
        end_time = meeting_data['endTime']
        
        # Create timezone for Indian Standard Time (IST)
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        
        start_datetime = datetime.datetime.combine(meeting_date, start_time)
        end_datetime = datetime.datetime.combine(meeting_date, end_time)
        
        # Set timezone to IST
        start_datetime = start_datetime.replace(tzinfo=ist_timezone)
        end_datetime = end_datetime.replace(tzinfo=ist_timezone)

        full_name = f"{meeting_data['firstName']} {meeting_data['lastName']}"
        
        event_body = {
            'summary': f"Meeting with {full_name}",
            'description': meeting_data['message'],
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'attendees': [
                {'email': meeting_data['email']}
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet_{start_datetime.strftime('%Y%m%d_%H%M%S')}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 30},
                    {'method': 'popup', 'minutes': 10}
                ]
            }
        }
        logger.info(f"Event body created: {event_body}")
        return event_body

def schedule_meeting(meeting_data: Dict[str, Any]) -> Optional[str]:
    """
    Schedule a Google Meet meeting with the provided details.
    Args:
        meeting_data: Dictionary containing meeting details
    Returns:
        Optional[str]: Google Meet link for online meetings, None for offline meetings
    Raises:
        HttpError: If the API request fails
        ValueError: If required meeting data is missing
    """
    logger.info(f"Scheduling meeting with data: {meeting_data}")
    
    if not meeting_data.get('isOnline'):
        logger.info("Offline meeting detected. No Google Meet link will be generated.")
        return None

    required_fields = ['firstName', 'lastName', 'email', 'startTime', 'endTime', 'date', 'message']
    missing_fields = [field for field in required_fields if not meeting_data.get(field)]
    if missing_fields:
        logger.error(f"Missing required fields: {', '.join(missing_fields)}")
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    try:
        calendar_service = GoogleCalendarService()
        event_body = calendar_service.create_event_body(meeting_data)
        
        logger.info("Inserting event into Google Calendar...")
        event_result = calendar_service.service.events().insert(
            calendarId='primary',
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates='all'
        ).execute()

        meet_link = event_result.get('hangoutLink')
        logger.info(f"Meeting scheduled successfully. Google Meet link: {meet_link}")
        return meet_link
    except HttpError as error:
        logger.error(f"HttpError occurred: {error}", exc_info=True)
        raise HttpError(error.resp, error.content) from error