import os
import json
import time
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_google_service():
    scopes = [
        'https://www.googleapis.com/auth/chat.spaces',
        'https://www.googleapis.com/auth/chat.spaces.readonly',
        'https://www.googleapis.com/auth/chat.delete',
        'https://www.googleapis.com/auth/chat.messages',
        'https://www.googleapis.com/auth/chat.messages.create',
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


def find_existing_space(service, display_name):
    try:
        result = service.spaces().list(pageSize=1000).execute()
        for space in result.get('spaces', []):
            if space.get('displayName') == display_name:
                return space['name']
    except Exception as e:
        print(f"  Warning: could not list spaces: {e}")
    return None


def create_space(service, display_name):
    existing = find_existing_space(service, display_name)
    if existing:
        print(f"  Found existing space '{display_name}', deleting...")
        try:
            service.spaces().delete(name=existing).execute()
            print(f"  Deleted: {existing}")
            time.sleep(1)
        except Exception as e:
            print(f"  Warning: could not delete space {existing}: {e}")

    try:
        space_payload = {"space": {"displayName": display_name, "spaceType": "SPACE"}}
        new_space = service.spaces().setup(body=space_payload).execute()
        return new_space['name']
    except Exception as e:
        print(f"Error, space wasnt created '{display_name}': {e}")
        return None


def upload_attachment(service, space_id, file_path, filename, mimetype):
    try:
        media = MediaFileUpload(file_path, mimetype=mimetype)
        result = service.media().upload(
            parent=space_id,
            body={'filename': filename},
            media_body=media
        ).execute()
        return result.get('attachmentDataRef')
    except Exception as e:
        print(f"  Failed to upload {filename}: {e}")
        return None


def upload_messages_from_file(service, space_id, file_path, channel_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    messages.reverse()
    count = 0
    media_dir = os.path.join('media', channel_name)

    for msg in messages:
        author = msg.get('author', 'Unknown')
        text = msg.get('text', '')
        date_str = msg.get('timestamp', '')[:16].replace('T', ' ')
        formatted_text = f"• *[{date_str}] {author}:*\n{text}"

        attachment_refs = []
        fallback_names = []

        for att in msg.get('attachments', []):
            fname = att['name']
            fpath = os.path.join(media_dir, fname)
            mimetype = att.get('mimetype', 'application/octet-stream')

            if os.path.exists(fpath):
                file_size = os.path.getsize(fpath)
                if file_size > 200 * 1024 * 1024:
                    print(f"  Skipping {fname}: exceeds 200MB limit")
                    fallback_names.append(fname)
                    continue

                ref = upload_attachment(service, space_id, fpath, fname, mimetype)
                if ref:
                    attachment_refs.append({
                        "contentName": fname,
                        "contentType": mimetype,
                        "attachmentDataRef": ref
                    })
                    time.sleep(1)
                else:
                    fallback_names.append(fname)
            else:
                fallback_names.append(fname)

        if fallback_names:
            formatted_text += "\n" + " ".join(f"[file: {n}]" for n in fallback_names)

        first_ref = attachment_refs[0] if attachment_refs else None
        extra_refs = attachment_refs[1:] if len(attachment_refs) > 1 else []

        body = {"text": formatted_text}
        if first_ref:
            body["attachment"] = [first_ref]

        try:
            service.spaces().messages().create(parent=space_id, body=body).execute()
            count += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"Error in message: {e}")

        for ref in extra_refs:
            try:
                service.spaces().messages().create(parent=space_id, body={"attachment": [ref]}).execute()
                time.sleep(0.4)
            except Exception as e:
                print(f"Error sending extra attachment: {e}")

    return count


def start_mass_migration():
    service = get_google_service()
    all_files = [f for f in os.listdir('.') if f.startswith('migration_') and f.endswith('.json')]
    print(f"{len(all_files)} files for migration found")

    for file_name in all_files:
        clean_name = file_name.replace('migration_', '').replace('.json', '')
        display_name = f"Archive: {clean_name}"
        print(f"\nStart to migrate chat: {clean_name}")
        space_id = create_space(service, display_name)
        if space_id:
            total = upload_messages_from_file(service, space_id, file_name, clean_name)
            print(f"Success! {total} messages in {clean_name}")
