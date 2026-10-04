import os
from providers.base_provider import BaseProvider

class UdemyProvider(BaseProvider):
    """
    Udemy Platform Integration Provider.
    """
    def __init__(self):
        super().__init__("Udemy")
        self.client_id = os.environ.get("UDEMY_CLIENT_ID", "")
        self.client_secret = os.environ.get("UDEMY_CLIENT_SECRET", "")

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, redirect_uri=None, state="state"):
        if not self.is_configured():
            return None, "Integration Not Configured: Missing UDEMY_CLIENT_ID in environment."
        return f"https://www.udemy.com/oauth2/authorize?client_id={self.client_id}", None

    def exchange_code_for_token(self, code, redirect_uri=None):
        if not self.is_configured():
            return None, "Integration Not Configured"
        return {"access_token": "mock_udemy_token"}, None

    def get_enrollments(self, access_token):
        return [], None

    def get_course_progress(self, access_token, external_course_id):
        return {"overall_progress": 0.0}, None
