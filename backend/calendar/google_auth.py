import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv()

SCOPES        = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8003/oauth/callback")
CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


def get_oauth_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow


def exchange_code_for_credentials(auth_code: str) -> Credentials:
    flow = get_oauth_flow()
    flow.fetch_token(code=auth_code)
    return flow.credentials


def get_authorization_url() -> str:
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url
