import os
import json
import requests
from datetime import datetime
from slack_sdk import WebClient
import certifi

def run_slack_export():
    os.environ['SSL_CERT_FILE'] = certifi.where()
    token = os.getenv("SLACK_USER_TOKEN")
    client = WebClient(token=token)

    try:
        print("Loading users from database...")
        u_res = client.users_list(include_deactivated=True)
        user_map = {
            u['id']: {
                "name": u.get('real_name', u['name']),
                "email": u.get('profile', {}).get('email', f"{u['name']}@placeholder.com")
            } for u in u_res['members']
        }

        print("Looking for open channels and chats...")
        conv_res = client.conversations_list(types="public_channel,private_channel,im")

        for conversation in conv_res['channels']:
            c_id = conversation['id']
            if conversation.get('is_im'):
                target_user = conversation.get('user')
                c_name = f"DM_with_{user_map.get(target_user, {'name': target_user})['name']}"
            else:
                c_name = conversation['name']

            print(f"Processing {c_name} (ID: {c_id})")
            history = client.conversations_history(channel=c_id, limit=1000)
            messages = history['messages']

            clean_messages = []
            for msg in messages:
                if 'user' in msg:
                    u_id = msg['user']
                    info = user_map.get(u_id, {"name": "Unknown", "email": "unknown@domain.com"})
                    dt = datetime.fromtimestamp(float(msg['ts']))

                    attachments = []
                    for f in msg.get('files', []):
                        url = f.get('url_private_download') or f.get('url_private')
                        if url:
                            attachments.append({
                                "url": url,
                                "name": f.get('name', 'file'),
                                "mimetype": f.get('mimetype', 'application/octet-stream')
                            })

                    clean_messages.append({
                        "text": msg.get('text', ''),
                        "author": info['name'],
                        "email": info['email'],
                        "timestamp": dt.isoformat() + "Z",
                        "attachments": attachments
                    })

            filename = f"migration_{c_name}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(clean_messages, f, ensure_ascii=False, indent=4)
            print(f"Saved in {filename}")

    except Exception as e:
        print(f"Error in Slack export: {e}")

    download_slack_files(token)


def download_slack_files(token):
    if not token:
        print("ERROR: SLACK_USER_TOKEN is empty, cannot download files")
        return

    headers = {"Authorization": f"Bearer {token}"}
    migration_files = [f for f in os.listdir('.') if f.startswith('migration_') and f.endswith('.json')]
    total_ok, total_fail = 0, 0

    for mf in migration_files:
        channel_name = mf.replace('migration_', '').replace('.json', '')
        with open(mf, 'r', encoding='utf-8') as f:
            messages = json.load(f)

        attachments_in_chat = [att for msg in messages for att in msg.get('attachments', [])]
        if not attachments_in_chat:
            continue

        media_dir = os.path.join('media', channel_name)
        os.makedirs(media_dir, exist_ok=True)
        print(f"Downloading {len(attachments_in_chat)} files for {channel_name}...")

        for attachment in attachments_in_chat:
            file_path = os.path.join(media_dir, attachment['name'])
            if os.path.exists(file_path):
                print(f"  Skip (exists): {attachment['name']}")
                total_ok += 1
                continue
            try:
                r = requests.get(attachment['url'], headers=headers, timeout=60)
                r.raise_for_status()
                with open(file_path, 'wb') as out:
                    out.write(r.content)
                print(f"  OK: {attachment['name']}")
                total_ok += 1
            except Exception as e:
                print(f"  FAIL: {attachment['name']} — {e}")
                total_fail += 1

    print(f"Files download done: {total_ok} ok, {total_fail} failed")
