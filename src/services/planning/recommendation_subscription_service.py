"""Recommendation subscription service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.recommendation_subscription_status import (
    RecommendationSubscriptionStatusEnum,
)
from google.ads.googleads.v20.enums.types.recommendation_type import (
    RecommendationTypeEnum,
)
from google.ads.googleads.v20.resources.types.recommendation_subscription import (
    RecommendationSubscription,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.services.recommendation_subscription_service import (
    RecommendationSubscriptionServiceClient,
)
from google.ads.googleads.v20.services.types.recommendation_subscription_service import (
    MutateRecommendationSubscriptionRequest,
    MutateRecommendationSubscriptionResponse,
    RecommendationSubscriptionOperation,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class RecommendationSubscriptionService:
    """Service for managing recommendation subscriptions."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[RecommendationSubscriptionServiceClient] = None

    @property
    def client(self) -> RecommendationSubscriptionServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "RecommendationSubscriptionService"
            )
        assert self._client is not None
        return self._client

    async def create_recommendation_subscription(
        self,
        ctx: Context,
        customer_id: str,
        recommendation_type: RecommendationTypeEnum.RecommendationType,
        status: RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
    ) -> Dict[str, Any]:
        """Subscribe to automatic application of a recommendation type.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            recommendation_type: The recommendation type to subscribe to
            status: Subscription status (ENABLED or PAUSED)

        Returns:
            Created subscription details
        """
        try:
            customer_id = format_customer_id(customer_id)

            subscription = RecommendationSubscription()
            subscription.type_ = recommendation_type
            subscription.status = status

            operation = RecommendationSubscriptionOperation()
            operation.create = subscription

            request = MutateRecommendationSubscriptionRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateRecommendationSubscriptionResponse = (
                self.client.mutate_recommendation_subscription(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created recommendation subscription for type {recommendation_type}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create recommendation subscription: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_recommendation_subscription(
        self,
        ctx: Context,
        customer_id: str,
        recommendation_type: str,
        status: RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
    ) -> Dict[str, Any]:
        """Update a recommendation subscription status.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            recommendation_type: The recommendation type string (for resource name)
            status: New subscription status

        Returns:
            Updated subscription details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/recommendationSubscriptions/{recommendation_type}"

            subscription = RecommendationSubscription()
            subscription.resource_name = resource_name
            subscription.status = status

            operation = RecommendationSubscriptionOperation()
            operation.update = subscription
            operation.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))

            request = MutateRecommendationSubscriptionRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_recommendation_subscription(request=request)

            await ctx.log(
                level="info",
                message=f"Updated recommendation subscription {recommendation_type}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update recommendation subscription: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_recommendation_subscriptions(
        self,
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List recommendation subscriptions.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of recommendation subscriptions
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = f"""
                SELECT
                    recommendation_subscription.resource_name,
                    recommendation_subscription.type,
                    recommendation_subscription.status,
                    recommendation_subscription.create_date_time,
                    recommendation_subscription.modify_date_time
                FROM recommendation_subscription
                LIMIT {limit}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            subscriptions = []
            for row in response:
                s = row.recommendation_subscription
                subscriptions.append(
                    {
                        "resource_name": s.resource_name,
                        "type": s.type_.name if s.type_ else "UNKNOWN",
                        "status": s.status.name if s.status else "UNKNOWN",
                        "create_date_time": s.create_date_time,
                        "modify_date_time": s.modify_date_time,
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(subscriptions)} recommendation subscriptions",
            )

            return subscriptions

        except Exception as e:
            error_msg = f"Failed to list recommendation subscriptions: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_recommendation_subscription_tools(
    service: RecommendationSubscriptionService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for recommendation subscription service."""
    tools = []

    async def create_recommendation_subscription(
        ctx: Context,
        customer_id: str,
        recommendation_type: str,
        status: str = "ENABLED",
    ) -> Dict[str, Any]:
        """Subscribe to automatic application of a recommendation type.

        Args:
            customer_id: The customer ID
            recommendation_type: Type of recommendation to subscribe - e.g.
                KEYWORD, RESPONSIVE_SEARCH_AD, CALL_EXTENSION, SITELINK,
                CALLOUT, TEXT_AD, TARGET_CPA_OPT_IN, MAXIMIZE_CONVERSIONS_OPT_IN,
                ENHANCED_CPC_OPT_IN, TARGET_ROAS_OPT_IN
            status: ENABLED or PAUSED

        Returns:
            Created subscription details
        """
        rec_type = getattr(
            RecommendationTypeEnum.RecommendationType, recommendation_type
        )
        sub_status = getattr(
            RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
            status,
        )
        return await service.create_recommendation_subscription(
            ctx=ctx,
            customer_id=customer_id,
            recommendation_type=rec_type,
            status=sub_status,
        )

    async def update_recommendation_subscription(
        ctx: Context,
        customer_id: str,
        recommendation_type: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update the status of a recommendation subscription.

        Args:
            customer_id: The customer ID
            recommendation_type: The recommendation type identifier
            status: New status - ENABLED or PAUSED

        Returns:
            Updated subscription details
        """
        sub_status = getattr(
            RecommendationSubscriptionStatusEnum.RecommendationSubscriptionStatus,
            status,
        )
        return await service.update_recommendation_subscription(
            ctx=ctx,
            customer_id=customer_id,
            recommendation_type=recommendation_type,
            status=sub_status,
        )

    async def list_recommendation_subscriptions(
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List recommendation subscriptions.

        Args:
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of recommendation subscriptions with their types and statuses
        """
        return await service.list_recommendation_subscriptions(
            ctx=ctx,
            customer_id=customer_id,
            limit=limit,
        )

    tools.extend(
        [
            create_recommendation_subscription,
            update_recommendation_subscription,
            list_recommendation_subscriptions,
        ]
    )
    return tools


def register_recommendation_subscription_tools(
    mcp: FastMCP[Any],
) -> RecommendationSubscriptionService:
    """Register recommendation subscription tools with the MCP server."""
    service = RecommendationSubscriptionService()
    tools = create_recommendation_subscription_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
