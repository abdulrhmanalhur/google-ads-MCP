"""Customer lifecycle goal service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.lifecycle_goals import (
    LifecycleGoalValueSettings,
)
from google.ads.googleads.v20.resources.types.customer_lifecycle_goal import (
    CustomerLifecycleGoal,
)
from google.ads.googleads.v20.services.services.customer_lifecycle_goal_service import (
    CustomerLifecycleGoalServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.customer_lifecycle_goal_service import (
    ConfigureCustomerLifecycleGoalsRequest,
    ConfigureCustomerLifecycleGoalsResponse,
    CustomerLifecycleGoalOperation,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CustomerLifecycleGoalService:
    """Service for managing customer lifecycle goals."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[CustomerLifecycleGoalServiceClient] = None

    @property
    def client(self) -> CustomerLifecycleGoalServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("CustomerLifecycleGoalService")
        assert self._client is not None
        return self._client

    async def configure_customer_lifecycle_goals(
        self,
        ctx: Context,
        customer_id: str,
        high_lifetime_value: Optional[float] = None,
        value: Optional[float] = None,
        is_create: bool = True,
    ) -> Dict[str, Any]:
        """Configure customer lifecycle goals.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            high_lifetime_value: Optional high lifetime value threshold
            value: Optional customer value
            is_create: Whether to create (True) or update (False)

        Returns:
            Configuration result
        """
        try:
            customer_id = format_customer_id(customer_id)

            goal = CustomerLifecycleGoal()

            if not is_create:
                goal.resource_name = f"customers/{customer_id}/customerLifecycleGoal"

            if high_lifetime_value is not None or value is not None:
                value_settings = LifecycleGoalValueSettings()
                if high_lifetime_value is not None:
                    value_settings.high_lifetime_value = high_lifetime_value
                if value is not None:
                    value_settings.value = value
                goal.customer_acquisition_goal_value_settings = value_settings

            update_mask_paths = []
            if high_lifetime_value is not None:
                update_mask_paths.append(
                    "customer_acquisition_goal_value_settings.high_lifetime_value"
                )
            if value is not None:
                update_mask_paths.append(
                    "customer_acquisition_goal_value_settings.value"
                )

            operation = CustomerLifecycleGoalOperation()
            if is_create:
                operation.create = goal
            else:
                operation.update = goal
                operation.update_mask.CopyFrom(
                    field_mask_pb2.FieldMask(paths=update_mask_paths)
                )

            request = ConfigureCustomerLifecycleGoalsRequest()
            request.customer_id = customer_id
            request.operation = operation

            response: ConfigureCustomerLifecycleGoalsResponse = (
                self.client.configure_customer_lifecycle_goals(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Configured customer lifecycle goals for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to configure customer lifecycle goals: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def get_customer_lifecycle_goal(
        self,
        ctx: Context,
        customer_id: str,
    ) -> Dict[str, Any]:
        """Get customer lifecycle goal settings.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID

        Returns:
            Customer lifecycle goal details
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    customer_lifecycle_goal.resource_name,
                    customer_lifecycle_goal.owner_customer,
                    customer_lifecycle_goal.customer_acquisition_goal_value_settings.high_lifetime_value,
                    customer_lifecycle_goal.customer_acquisition_goal_value_settings.value
                FROM customer_lifecycle_goal
                LIMIT 1
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            for row in response:
                g = row.customer_lifecycle_goal
                return {
                    "resource_name": g.resource_name,
                    "owner_customer": g.owner_customer,
                    "high_lifetime_value": g.customer_acquisition_goal_value_settings.high_lifetime_value
                    if g.customer_acquisition_goal_value_settings
                    else None,
                    "value": g.customer_acquisition_goal_value_settings.value
                    if g.customer_acquisition_goal_value_settings
                    else None,
                }

            return {}

        except Exception as e:
            error_msg = f"Failed to get customer lifecycle goal: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_lifecycle_goal_tools(
    service: CustomerLifecycleGoalService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for customer lifecycle goal service."""
    tools = []

    async def configure_customer_lifecycle_goals(
        ctx: Context,
        customer_id: str,
        high_lifetime_value: Optional[float] = None,
        value: Optional[float] = None,
        is_create: bool = True,
    ) -> Dict[str, Any]:
        """Configure customer lifecycle goals for customer acquisition.

        Args:
            customer_id: The customer ID
            high_lifetime_value: Optional high lifetime value threshold in micros
            value: Optional customer acquisition value in micros
            is_create: True to create new settings, False to update existing

        Returns:
            Configuration result
        """
        return await service.configure_customer_lifecycle_goals(
            ctx=ctx,
            customer_id=customer_id,
            high_lifetime_value=high_lifetime_value,
            value=value,
            is_create=is_create,
        )

    async def get_customer_lifecycle_goal(
        ctx: Context,
        customer_id: str,
    ) -> Dict[str, Any]:
        """Get customer lifecycle goal settings.

        Args:
            customer_id: The customer ID

        Returns:
            Customer lifecycle goal settings including value thresholds
        """
        return await service.get_customer_lifecycle_goal(
            ctx=ctx,
            customer_id=customer_id,
        )

    tools.extend(
        [
            configure_customer_lifecycle_goals,
            get_customer_lifecycle_goal,
        ]
    )
    return tools


def register_customer_lifecycle_goal_tools(
    mcp: FastMCP[Any],
) -> CustomerLifecycleGoalService:
    """Register customer lifecycle goal tools with the MCP server."""
    service = CustomerLifecycleGoalService()
    tools = create_customer_lifecycle_goal_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
