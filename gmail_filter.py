from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import base64
import email
import requests
import os

# Prediction Endpoint
API_URL = "http://127.0.0.1:8000/predict"

# Gmail API permissions allow reading, modifying, and moving emails
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def authenticate_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token) # avoids re-authenticating every time.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: # credentials are expired but have a refresh token
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret_88433899415-32r8ugbsq9rg449lpoujcnavmh8jeiad.apps.googleusercontent.com.json", SCOPES) # if no credentials exist or refresh isn’t possible, I will authenticate via OAuth 
            creds = flow.run_local_server(port=8080) # Opens a browser to log in and authorize My app.
        with open("token.pickle", "wb") as token:  #   Saves refreshed or newly obtained credentials to token.pickle
            pickle.dump(creds, token)
    service = build("gmail", "v1", credentials=creds)
    return service

def get_unread_emails(service):   # Returns a list of message IDs
    results = service.users().messages().list(userId="me", labelIds=["UNREAD"]).execute()
    messages = results.get("messages", []) 
    return messages

def get_email_text(service, msg_id):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg["payload"]
    parts = payload.get("parts")
    text = ""
    if parts:
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                text = base64.urlsafe_b64decode(data).decode("utf-8")
                break
    else:
        data = payload["body"].get("data")
        if data:
            text = base64.urlsafe_b64decode(data).decode("utf-8")
    return text, msg

def move_to_spam(service, msg_id):
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]}
    ).execute()

def classify_and_filter_emails():
    service = authenticate_gmail()
    messages = get_unread_emails(service)
    print(f"Found {len(messages)} unread emails.")

    for msg in messages:
        msg_id = msg["id"]
        text, full_msg = get_email_text(service, msg_id)
        if not text.strip(): #If the email text is empty, skip it
            continue

        # Send text to /predict endpoint
        response = requests.post(API_URL, json={"text": text})
        if response.status_code == 200:
            result = response.json()
            label = result["prediction"]
            prob = result["probability"]

            print(f"Email: {full_msg['snippet'][:60]}...")
            print(f"→ Prediction: {label} (prob={prob:.3f})")

            if label == "spam":
                move_to_spam(service, msg_id)
                print("Moved to Spam\n")
            else:
                print("Kept in Inbox\n")

