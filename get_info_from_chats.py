import os
import json
from datetime import datetime
from slack_sdk import WebClient
import certifi

def run_slack_export():
    os.environ['SSL_CERT_FILE'] = certifi.where()
    client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))

    try:
        print("Loading users database...")
        u_res = client.users_list()
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

                    clean_messages.append({
                        "text": msg.get('text', ''),
                        "author": info['name'],
                        "email": info['email'],
                        "timestamp": dt.isoformat() + "Z"
                    })

            filename = f"migration_{c_name}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(clean_messages, f, ensure_ascii=False, indent=4)
            print(f"Saved in {filename}")

    except Exception as e:
        print(f"Error in Slack export: {e}")