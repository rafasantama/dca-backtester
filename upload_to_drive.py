from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Get Google Drive service with authentication."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_file(service, filename, filepath, mime_type='text/csv'):
    """Upload a file to Google Drive."""
    file_metadata = {
        'name': filename,
        'mimeType': mime_type
    }
    
    media = MediaFileUpload(
        filepath,
        mimetype=mime_type,
        resumable=True
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print(f'File ID: {file.get("id")}')
    return file.get('id')

def main():
    """Upload all CSV files to Google Drive."""
    service = get_google_drive_service()
    
    # Dictionary to store file IDs
    file_ids = {}
    
    # Upload each CSV file
    for symbol in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'MATIC', 'LINK']:
        filepath = f'data/{symbol}.csv'
        if os.path.exists(filepath):
            file_id = upload_file(service, f'{symbol}.csv', filepath)
            file_ids[symbol] = file_id
    
    # Print the file IDs for the GoogleDriveClient
    print("\nFile IDs for GoogleDriveClient:")
    print("self.file_ids = {")
    for symbol, file_id in file_ids.items():
        print(f'    "{symbol}": "{file_id}",')
    print("}")

if __name__ == '__main__':
    main() 