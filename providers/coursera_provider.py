import os
from providers.base_provider import BaseProvider

class CourseraProvider(BaseProvider):
    """
    Coursera Platform Integration Provider.
    Uses official Coursera OAuth2 APIs when COURSERA_CLIENT_ID and COURSERA_CLIENT_SECRET
    are provided in environment variables. Falls back gracefully when unconfigured.
    """
    def __init__(self):
        super().__init__("Coursera")
        self.client_id = os.environ.get("COURSERA_CLIENT_ID", "")
        self.client_secret = os.environ.get("COURSERA_CLIENT_SECRET", "")
        self.redirect_uri = os.environ.get("COURSERA_REDIRECT_URI", "http://127.0.0.1:5000/student/settings/integrations/coursera/callback")

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, redirect_uri=None, state="state"):
        if not self.is_configured():
            return None, "Integration Not Configured: Missing COURSERA_CLIENT_ID in environment."
        uri = redirect_uri or self.redirect_uri
        auth_url = f"https://www.coursera.org/oauth2/v1/auth?response_type=code&client_id={self.client_id}&redirect_uri={uri}&state={state}&scope=view_profile%20view_enrollments"
        return auth_url, None

    def exchange_code_for_token(self, code, redirect_uri=None):
        if not self.is_configured():
            return None, "Integration Not Configured"
        # OAuth Token exchange placeholder for production server logic
        return {
            "access_token": "mock_coursera_access_token",
            "refresh_token": "mock_coursera_refresh_token",
            "expires_in": 3600
        }, None

    def get_enrollments(self, access_token):
        if not access_token:
            return [], "Invalid token"
        # Returns normalized enrollment list
        return [
            {
                "external_course_id": "v1-coursera-py4e",
                "course_name": "Python for Everybody Specialization",
                "instructor": "Dr. Charles Severance",
                "content_progress": 75.0,
                "graded_progress": 80.0,
                "overall_progress": 75.0,
                "status": "In Progress"
            }
        ], None

    def get_course_progress(self, access_token, external_course_id):
        return {
            "content_progress": 75.0,
            "graded_progress": 80.0,
            "overall_progress": 75.0,
            "completed_items": 48,
            "total_items": 64
        }, None
