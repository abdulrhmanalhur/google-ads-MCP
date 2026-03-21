"""Smart campaign setting service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.smart_campaign_setting import (
    SmartCampaignSetting,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.services.smart_campaign_setting_service import (
    SmartCampaignSettingServiceClient,
)
from google.ads.googleads.v20.services.types.smart_campaign_setting_service import (
    GetSmartCampaignStatusRequest,
    GetSmartCampaignStatusResponse,
    MutateSmartCampaignSettingsRequest,
    MutateSmartCampaignSettingsResponse,
    SmartCampaignSettingOperation,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class SmartCampaignSettingService:
    """Service for managing Smart campaign settings."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[SmartCampaignSettingServiceClient] = None

    @property
    def client(self) -> SmartCampaignSettingServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("SmartCampaignSettingService")
        assert self._client is not None
        return self._client

    async def get_smart_campaign_status(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get the status of a Smart campaign.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The Smart campaign ID

        Returns:
            Smart campaign status details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/smartCampaignSettings/{campaign_id}"
            )

            request = GetSmartCampaignStatusRequest()
            request.resource_name = resource_name

            response: GetSmartCampaignStatusResponse = (
                self.client.get_smart_campaign_status(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Retrieved Smart campaign status for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to get Smart campaign status: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_smart_campaign_setting(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        final_url: Optional[str] = None,
        advertising_language_code: Optional[str] = None,
        business_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        phone_country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update Smart campaign settings.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The Smart campaign ID
            final_url: Optional final landing page URL
            advertising_language_code: Optional language code (e.g., 'en')
            business_name: Optional business name
            phone_number: Optional phone number
            phone_country: Optional phone country code

        Returns:
            Updated settings details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/smartCampaignSettings/{campaign_id}"
            )

            setting = SmartCampaignSetting()
            setting.resource_name = resource_name

            update_mask_paths = []

            if final_url is not None:
                setting.final_url = final_url
                update_mask_paths.append("final_url")

            if advertising_language_code is not None:
                setting.advertising_language_code = advertising_language_code
                update_mask_paths.append("advertising_language_code")

            if business_name is not None:
                setting.business_name = business_name
                update_mask_paths.append("business_name")

            if phone_number is not None or phone_country is not None:
                phone = SmartCampaignSetting.PhoneNumber()
                if phone_number:
                    phone.phone_number = phone_number
                if phone_country:
                    phone.country_code = phone_country
                setting.phone_number = phone
                update_mask_paths.append("phone_number")

            operation = SmartCampaignSettingOperation()
            operation.update = setting
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=update_mask_paths)
            )

            request = MutateSmartCampaignSettingsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateSmartCampaignSettingsResponse = (
                self.client.mutate_smart_campaign_settings(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated Smart campaign settings for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update Smart campaign settings: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_smart_campaign_settings(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List Smart campaign settings.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of Smart campaign settings
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    smart_campaign_setting.resource_name,
                    smart_campaign_setting.campaign,
                    smart_campaign_setting.advertising_language_code,
                    smart_campaign_setting.final_url,
                    smart_campaign_setting.business_name,
                    smart_campaign_setting.phone_number.phone_number,
                    smart_campaign_setting.phone_number.country_code
                FROM smart_campaign_setting
            """

            conditions = []
            if campaign_id:
                campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"
                conditions.append(
                    f"smart_campaign_setting.campaign = '{campaign_resource}'"
                )

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            settings = []
            for row in response:
                s = row.smart_campaign_setting
                settings.append(
                    {
                        "resource_name": s.resource_name,
                        "campaign": s.campaign,
                        "advertising_language_code": s.advertising_language_code,
                        "final_url": s.final_url,
                        "business_name": s.business_name,
                        "phone_number": s.phone_number.phone_number
                        if s.phone_number
                        else None,
                        "phone_country": s.phone_number.country_code
                        if s.phone_number
                        else None,
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(settings)} Smart campaign settings",
            )

            return settings

        except Exception as e:
            error_msg = f"Failed to list Smart campaign settings: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_smart_campaign_setting_tools(
    service: SmartCampaignSettingService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for Smart campaign setting service."""
    tools = []

    async def get_smart_campaign_status(
        ctx: Context,
        customer_id: str,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get the status of a Smart campaign.

        Args:
            customer_id: The customer ID
            campaign_id: The Smart campaign ID

        Returns:
            Smart campaign status including eligibility and details
        """
        return await service.get_smart_campaign_status(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )

    async def update_smart_campaign_setting(
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        final_url: Optional[str] = None,
        advertising_language_code: Optional[str] = None,
        business_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        phone_country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update Smart campaign settings.

        Args:
            customer_id: The customer ID
            campaign_id: The Smart campaign ID
            final_url: Optional landing page URL
            advertising_language_code: Optional language code (e.g., 'en')
            business_name: Optional business name
            phone_number: Optional phone number
            phone_country: Optional phone country code (e.g., 'US')

        Returns:
            Updated settings details
        """
        return await service.update_smart_campaign_setting(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            final_url=final_url,
            advertising_language_code=advertising_language_code,
            business_name=business_name,
            phone_number=phone_number,
            phone_country=phone_country,
        )

    async def list_smart_campaign_settings(
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List Smart campaign settings.

        Args:
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of Smart campaign settings
        """
        return await service.list_smart_campaign_settings(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            limit=limit,
        )

    tools.extend(
        [
            get_smart_campaign_status,
            update_smart_campaign_setting,
            list_smart_campaign_settings,
        ]
    )
    return tools


def register_smart_campaign_setting_tools(
    mcp: FastMCP[Any],
) -> SmartCampaignSettingService:
    """Register Smart campaign setting tools with the MCP server."""
    service = SmartCampaignSettingService()
    tools = create_smart_campaign_setting_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
