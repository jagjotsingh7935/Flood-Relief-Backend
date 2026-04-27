# doctorApp/management/commands/authorize_google.py

from django.core.management.base import BaseCommand
from django.conf import settings
from google_auth_oauthlib.flow import InstalledAppFlow
from doctorApp.models import GoogleToken
from urllib.parse import urlparse, parse_qs
import os
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Run Google OAuth 2.0 flow manually to obtain and save refresh token for the app'

    def handle(self, *args, **options):
        # Your existing constants
        SCOPES = ['https://www.googleapis.com/auth/calendar.events']  # Change/add scopes as needed
        CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, 'credentials.json')
        REDIRECT_URI = 'https://metabolicresetwithbob.com/oauth2callback'  # Must match exactly in Google Console

        try:
            # Load the client secrets (your credentials.json - web type)
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                scopes=SCOPES
            )

            # Important: Set the redirect URI manually (for web client credentials)
            flow.redirect_uri = REDIRECT_URI

            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',      # Required to get refresh token
                include_granted_scopes='true',
                prompt='consent'            # Forces refresh token even on re-auth
            )

            self.stdout.write("Please visit this URL to authorize the application:")
            self.stdout.write(self.style.SUCCESS(auth_url))
            self.stdout.write("\nAfter granting permission, you will be redirected to:")
            self.stdout.write(f"{REDIRECT_URI}?code=...\n")

            redirect_response = input("Paste the FULL redirect URL here: ").strip()

            # Extract the authorization code from the URL
            parsed_url = urlparse(redirect_response)
            query_params = parse_qs(parsed_url.query)
            code = query_params.get('code', [None])[0]

            if not code:
                raise ValueError("No authorization code found in the redirect URL.")

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Convert credentials to dict and save to your model
            token_data = json.loads(credentials.to_json())

            GoogleToken.objects.update_or_create(
                id=1,  # Assuming you're storing a single app-wide token
                defaults={
                    'token': token_data['token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'token_uri': token_data['token_uri'],
                    'client_id': token_data['client_id'],
                    'client_secret': token_data['client_secret'],
                    'scopes': token_data['scopes'],
                    'expiry': datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00')) if token_data.get('expiry') else None,
                }
            )

            self.stdout.write(self.style.SUCCESS('Authentication successful! Token saved to GoogleToken model.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: 'credentials.json' not found at {CREDENTIALS_PATH}"))
            self.stdout.write("Make sure the file is in your project root (same level as manage.py).")

        except ValueError as ve:
            self.stdout.write(self.style.ERROR(f"Error: {str(ve)}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error during OAuth flow: {str(e)}"))