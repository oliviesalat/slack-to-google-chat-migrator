import os
import json
import time
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_google_service():
    scopes = [
        'https://www.googleapis.com/auth/chat.spaces',
        'https://www.googleapis.com/auth/chat.messages.create'
    ]
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('chat', 'v1', credentials=creds)

def create_space(service, display_name):
    try:
        space_payload = {"space": {"displayName": display_name, "spaceType": "SPACE"}}
        new_space = service.spaces().setup(body=space_payload).execute()
        return new_space['name']
    except Exception as e:
        print(f"Error, space didnt created '{display_name}': {e}")
        return None

def upload_messages_from_file(service, space_id, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    messages.reverse()
    count = 0
    for msg in messages:
        author = msg.get('author', 'Unknown')
        text = msg.get('text', '')
        date_str = msg.get('timestamp', '')[:16].replace('T', ' ')
        formatted_text = f"• *[{date_str}] {author}:*\n{text}"
        try:
            service.spaces().messages().create(parent=space_id, body={"text": formatted_text}).execute()
            count += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"Error in message: {e}")
    return count

def start_mass_migration():
    service = get_google_service()
    all_files = [f for f in os.listdir('.') if f.startswith('migration_') and f.endswith('.json')]
    print(f"{len(all_files)} files for migration found")

    for file_name in all_files:
        clean_name = file_name.replace('migration_', '').replace('.json', '')
        print(f"\nStart to migrate chat: {clean_name}")
        space_id = create_space(service, f"Archive: {clean_name}")
        if space_id:
            total = upload_messages_from_file(service, space_id, file_name)
            print(f"Success! {total} messages in {clean_name}")