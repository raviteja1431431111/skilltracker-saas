from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Abstract Base Class for External Education Platform Providers.
    Provides standard interface for OAuth authorization, enrollment fetching,
    progress tracking, and certificate verification.
    """
    def __init__(self, platform_name):
        self.platform_name = platform_name

    @abstractmethod
    def is_configured(self):
        """Check if platform API credentials / OAuth config exist in environment."""
        pass

    @abstractmethod
    def get_authorization_url(self, redirect_uri, state):
        """Generate OAuth authorization URL for user consent."""
        pass

    @abstractmethod
    def exchange_code_for_token(self, code, redirect_uri):
        """Exchange authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    def get_enrollments(self, access_token):
        """Fetch active user enrollments from external API."""
        pass

    @abstractmethod
    def get_course_progress(self, access_token, external_course_id):
        """Fetch detailed course progress metrics (content %, graded %, overall %)."""
        pass
