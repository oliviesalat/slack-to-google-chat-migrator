# Slack to Google Chat Migration Tool

This tool automates the process of exporting message history from Slack channels (including DMs) and importing them into
Google Chat Spaces, including file attachments.

The script creates new Spaces in Google Chat and migrates messages using the following template:
• [YYYY-MM-DD HH:MM] Author Name: Message Text

Example:
• [2022-10-24 15:29] John Smith: some message text...

---

## Prerequisites & Configuration

### 1. Slack Setup (API Configuration)

You need to create a Slack App at https://api.slack.com/apps to get your token.

* **App Type:** Create an app "From scratch".
* **Scopes:** Navigate to "OAuth & Permissions" and add the following "User Token Scopes":
    * channels:history — to read public channel messages.
    * groups:history — to read private channel messages.
    * im:history — to read direct messages (DMs).
    * users:read — to map User IDs to real names.
    * files:read — to download file attachments.
* **Installation:** Install the app to your workspace and copy the "User OAuth Token" (starts with xoxp-).

### 2. Google Cloud Setup (OAuth Configuration)

1. **Enable API:** Go to Google Cloud Console, create a project, and enable the "Google Chat API".
2. **OAuth Consent Screen:**
    * Set "User Type" to "Internal" (recommended for Workspace/University accounts).
    * Go to **API & Services → OAuth consent screen → Data access → Add/Remove Scopes** and add all scopes listed below.
3. **Required Google OAuth Scopes:**
    * https://www.googleapis.com/auth/chat.spaces
    * https://www.googleapis.com/auth/chat.spaces.readonly
    * https://www.googleapis.com/auth/chat.delete
    * https://www.googleapis.com/auth/chat.messages
    * https://www.googleapis.com/auth/chat.messages.create
4. **Credentials:**
    * Create "OAuth client ID" -> "Desktop Application".
    * Download the JSON file, rename it to client_secrets.json, and place it in the project root.

> **Note:** If you previously ran the script with fewer scopes, delete `token.pickle` before re-running so the OAuth flow requests the updated scope set.

---

## Installation & Setup

### 1. Prepare Environment

Run these commands in your terminal:

    # Create virtual environment
    python -m venv .venv

    # Activate environment (macOS/Linux)
    source .venv/bin/activate
    
    # OR Activate environment (Windows)
    .venv\Scripts\activate

    # Install required packages
    pip install -r requirements.txt

### 2. Configure Environment Variables

Create a file named ".env" in the project root and paste your token:

    SLACK_USER_TOKEN=xoxp-your-slack-token-here

---

## How to Use

Run the migration using the main entry point:

    python main.py

### Process Flow:

1. **Authorization:** On the first run, a browser tab will open. Log in with your Google account to generate token.pickle.
2. **Phase 1 (Export):** The script fetches history from all accessible Slack chats and saves them as migration_*.json. File attachments are downloaded into the media/ directory.
3. **Phase 2 (Import):** The script reads the exported files, creates corresponding Spaces in Google Chat (e.g., Archive: general), uploads messages, and attaches files directly to messages. If a space with the same name already exists, it is deleted and recreated to avoid duplicates.

### Cleanup

After a successful migration, remove all temporary files (migration JSON files and downloaded media):

    python clean.py

This removes `migration_*.json` files and the `media/` directory. It does not touch `token.pickle` or `client_secrets.json`.

---

## Technical Details

* Security: client_secrets.json, .env, and token.pickle are sensitive files. They are excluded from Git via .gitignore.
* Rate Limiting: Built-in delays (0.4s – 1.0s) ensure the script doesn't get blocked by Google or Slack API protections.
* Structure Preservation: The script preserves author names and original timestamps.
* User Mapping: If a Slack user's email is missing or hidden by privacy settings, the system automatically assigns a placeholder: "unknown@domain.com".
* File Attachments: Files up to 200 MB are uploaded directly to Google Chat. Files exceeding the limit or of blocked types are noted as [file: filename] in the message text.
* Deduplication: Before creating a space, the script checks if a space with the same display name already exists and deletes it first.

---

## Project Structure

* main.py — Orchestrates the export and import phases.
* get_info_from_chats.py — Extracts messages and downloads file attachments from Slack API.
* import_to_google.py — Manages Google Chat Space creation, deduplication, and message/file upload.
* clean.py — Removes temporary migration files after a successful migration.
