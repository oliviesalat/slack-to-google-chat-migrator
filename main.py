import os
from dotenv import load_dotenv
from get_info_from_chats import run_slack_export
from import_to_google import start_mass_migration


def main():
    load_dotenv()

    print("=== Phase 1: Exporting data from Slack ===")
    if not os.getenv("SLACK_USER_TOKEN"):
        print("Error: SLACK_USER_TOKEN not found in .env")
        return

    run_slack_export()

    print("\n=== Phase 2: Importing data to Google Chat ===")
    if os.path.exists('client_secrets.json'):
        start_mass_migration()
    else:
        print("Error: client_secrets.json not found! Please provide OAuth credentials.")


if __name__ == "__main__":
    main()