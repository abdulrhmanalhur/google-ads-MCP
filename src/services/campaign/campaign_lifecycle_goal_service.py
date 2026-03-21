"""Campaign lifecycle goal service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.customer_acquisition_optimization_mode import (
    CustomerAcquisitionOptimizationModeEnum,
)
from google.ads.googleads.v20.resources.types.campaign_lifecycle_goal import (
    CampaignLifecycleGoal,
    CustomerAcquisitionGoalSettings,
)
from google.ads.googleads.v20.services.services.campaign_lifecycle_goal_service import (
    CampaignLifecycleGoalServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.campaign_lifecycle_goal_service import (
    CampaignLifecycleGoalOperation,
    ConfigureCampaignLifecycleGoalsRequest,
    ConfigureCampaignLifecycleGoalsResponse,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CampaignLifecycleGoalService:
    """Service for managing campaign lifecycle goals."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[CampaignLifecycleGoalServiceClient] = None

    @property
    def client(self) -> CampaignLifecycleGoalServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("CampaignLifecycleGoalService")
        assert self._client is not None
        return self._client

    async def configure_campaign_lifecycle_goals(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode,
        is_create: bool = True,
    ) -> Dict[str, Any]:
        """Configure campaign lifecycle goals.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: The campaign ID
            optimization_mode: Customer acquisition optimization mode
            is_create: Whether to create (True) or update (False)

        Returns:
            Configuration result
        """
        try:
            customer_id = format_customer_id(customer_id)
            campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"

            campaign_lifecycle_goal = CampaignLifecycleGoal()

            if is_create:
                campaign_lifecycle_goal.campaign = campaign_resource
            else:
                resource_name = (
                    f"customers/{customer_id}/campaignLifecycleGoal/{campaign_id}"
                )
                campaign_lifecycle_goal.resource_name = resource_name

            goal_settings = CustomerAcquisitionGoalSettings()
            goal_settings.optimization_mode = optimization_mode
            campaign_lifecycle_goal.customer_acquisition_goal_settings = goal_settings

            operation = CampaignLifecycleGoalOperation()
            if is_create:
                operation.create = campaign_lifecycle_goal
            else:
                operation.update = campaign_lifecycle_goal
                operation.update_mask.CopyFrom(
                    field_mask_pb2.FieldMask(
                        paths=["customer_acquisition_goal_settings.optimization_mode"]
                    )
                )

            request = ConfigureCampaignLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation

            response: ConfigureCampaignLifecycleGoalsResponse = (
                self.client.configure_campaign_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Configured lifecycle goals for campaign {campaign_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to configure campaign lifecycle goals: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_campaign_lifecycle_goals(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign lifecycle goals.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of campaign lifecycle goals
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    campaign_lifecycle_goal.resource_name,
                    campaign_lifecycle_goal.campaign,
                    campaign_lifecycle_goal.customer_acquisition_goal_settings.optimization_mode
                FROM campaign_lifecycle_goal
            """

            conditions = []
            if campaign_id:
                campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"
                conditions.append(
                    f"campaign_lifecycle_goal.campaign = '{campaign_resource}'"
                )

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            goals = []
            for row in response:
                g = row.campaign_lifecycle_goal
                goals.append(
                    {
                        "resource_name": g.resource_name,
                        "campaign": g.campaign,
                        "optimization_mode": g.customer_acquisition_goal_settings.optimization_mode.name
                        if g.customer_acquisition_goal_settings.optimization_mode
                        else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(goals)} campaign lifecycle goals",
            )

            return goals

        except Exception as e:
            error_msg = f"Failed to list campaign lifecycle goals: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_campaign_lifecycle_goal_tools(
    service: CampaignLifecycleGoalService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for campaign lifecycle goal service."""
    tools = []

    async def configure_campaign_lifecycle_goals(
        ctx: Context,
        customer_id: str,
        campaign_id: str,
        optimization_mode: str,
        is_create: bool = True,
    ) -> Dict[str, Any]:
        """Configure campaign lifecycle goals for customer acquisition.

        Args:
            customer_id: The customer ID
            campaign_id: The campaign ID
            optimization_mode: Optimization mode - OPTIMIZE_NEW_CUSTOMER_ACQUISITION_GOAL,
                OPTIMIZE_NEW_CUSTOMER_ACQUISITION_GOAL_ONLY, or UNSPECIFIED
            is_create: True to create new, False to update existing

        Returns:
            Configuration result
        """
        mode_enum = getattr(
            CustomerAcquisitionOptimizationModeEnum.CustomerAcquisitionOptimizationMode,
            optimization_mode,
        )
        return await service.configure_campaign_lifecycle_goals(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            optimization_mode=mode_enum,
            is_create=is_create,
        )

    async def list_campaign_lifecycle_goals(
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign lifecycle goals.

        Args:
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of campaign lifecycle goals
        """
        return await service.list_campaign_lifecycle_goals(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            limit=limit,
        )

    tools.extend(
        [
            configure_campaign_lifecycle_goals,
            list_campaign_lifecycle_goals,
        ]
    )
    return tools


def register_campaign_lifecycle_goal_tools(
    mcp: FastMCP[Any],
) -> CampaignLifecycleGoalService:
    """Register campaign lifecycle goal tools with the MCP server."""
    service = CampaignLifecycleGoalService()
    tools = create_campaign_lifecycle_goal_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
