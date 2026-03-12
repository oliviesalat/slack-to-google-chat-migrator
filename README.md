# Slack to Google Chat Migration Tool

This tool automates the process of exporting message history from Slack channels (including DMs) and importing them into
Google Chat Spaces.

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
* **Installation:** Install the app to your workspace and copy the "User OAuth Token" (starts with xoxp-).

### 2. Google Cloud Setup (OAuth Configuration)

1. **Enable API:** Go to Google Cloud Console, create a project, and enable the "Google Chat API".
2. **OAuth Consent Screen:**
    * Set "User Type" to "Internal" (recommended for Workspace/University accounts).
    * Add scopes: https://www.googleapis.com/auth/chat.spaces and https://www.googleapis.com/auth/chat.messages.create.
3. **Credentials:**
    * Create "OAuth client ID" -> "Desktop Application".
    * Download the JSON file, rename it to client_secrets.json, and place it in the project root.

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

1. Authorization: On the first run, a browser tab will open. Log in with your university account to generate
   token.pickle.
2. Phase 1 (Export): The script fetches history from all accessible Slack chats and saves them as migration_*.json.
3. Phase 2 (Import): The script reads these files, creates corresponding Spaces in Google Chat (e.g., Archive: general),
   and uploads messages.

---

## Technical Details

* Security: client_secrets.json, .env, and token.pickle are sensitive files. They are excluded from Git via .gitignore.
* Rate Limiting: Built-in delays (0.4s – 1.0s) ensure the script doesn't get blocked by Google or Slack API protections.
* Structure Preservation: The script preserves author names and original timestamps.

---

## Project Structure

* main.py — Orchestrates the export and import phases.
* get_info_from_chats.py — Extracts data from Slack API.
* import_to_google.py — Manages Google Chat Space creation and message injection.