"""Google Ads SDK client for MCP server."""

import os
from typing import Optional

from google.ads.googleads.client import GoogleAdsClient

from src.utils import get_logger

logger = get_logger(__name__)


class GoogleAdsSdkClient:
    """SDK client for Google Ads with OAuth2 authentication."""

    def __init__(self):
        """Initialize the SDK client from environment variables."""
        self._client: Optional[GoogleAdsClient] = None

    @property
    def client(self) -> GoogleAdsClient:
        """Get or create the Google Ads client."""
        if self._client is None:
            client_config = {
                "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
                "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
                "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
                "use_proto_plus": True,
            }

            login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            if login_customer_id:
                client_config["login_customer_id"] = login_customer_id.replace("-", "")

            self._client = GoogleAdsClient.load_from_dict(client_config)
            logger.info("Google Ads SDK client initialized successfully")

        return self._client

    def close(self) -> None:
        """Close the client and clean up resources."""
        if self._client:
            # The SDK client doesn't have an explicit close method
            # but we can clear the reference
            self._client = None
            logger.info("Google Ads SDK client closed")


# Global client instance
_sdk_client: Optional[GoogleAdsSdkClient] = None


def get_sdk_client() -> GoogleAdsSdkClient:
    """Get the global SDK client instance."""
    global _sdk_client
    if _sdk_client is None:
        raise RuntimeError("SDK client not initialized. Call set_sdk_client first.")
    return _sdk_client


def set_sdk_client(client: GoogleAdsSdkClient) -> None:
    """Set the global SDK client instance."""
    global _sdk_client
    _sdk_client = client
