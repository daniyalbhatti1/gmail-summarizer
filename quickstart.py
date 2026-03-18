import os.path
import os
import base64

from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from dotenv import load_dotenv

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", q="is:unread newer_than:1d -category:promotions").execute()
    messages = results.get("messages", [])

    emails = []

    for msg in messages:
        full_msg = service.users().messages().get(
            userId="me",
            id=msg["id"]
        ).execute()

        headers = full_msg["payload"]["headers"]

        subject = ""
        sender = ""

        for h in headers:
            if h["name"] == "Subject":
                subject = h["value"]
            elif h["name"] == "From":
                sender = h["value"]

        snippet = full_msg["snippet"]

        email_text = f"""
        --- EMAIL START ---
        From: {sender}
        Subject: {subject}
        Snippet: {snippet}
        --- EMAIL END ---
        """

        emails.append(email_text)

    combined = "\n".join(emails)

    #print(combined)


  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")
  
  summary = gpt(combined)
  send_email(service, os.environ["EMAIL"], "Morning Email Summaries", summary)

def gpt(combined):
    load_dotenv()

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    prompt = f"""
    Summarize these emails into:
    - Urgent
    - Action items
    - Low priority
    - Key updates

    Emails:
    {combined}
    """

    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt
    )

    summary = response.output_text
    return summary

def send_email(service, to_email, subject, body_text):
    message = MIMEText(body_text)
    message["to"] = to_email
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_body = {
        "raw": raw_message
    }

    service.users().messages().send(
        userId="me",
        body=send_body
    ).execute()



if __name__ == "__main__":
  main()