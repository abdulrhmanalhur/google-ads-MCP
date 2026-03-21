"""Campaign budget service - additional operations for listing and removing budgets."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.campaign_budget_service import (
    CampaignBudgetServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.campaign_budget_service import (
    CampaignBudgetOperation,
    MutateCampaignBudgetsRequest,
    MutateCampaignBudgetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CampaignBudgetService:
    """Service for listing and removing campaign budgets."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[CampaignBudgetServiceClient] = None

    @property
    def client(self) -> CampaignBudgetServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("CampaignBudgetService")
        assert self._client is not None
        return self._client

    async def list_campaign_budgets(
        self,
        ctx: Context,
        customer_id: str,
        include_removed: bool = False,
        explicitly_shared_only: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign budgets.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            include_removed: Whether to include removed budgets
            explicitly_shared_only: If True, only return explicitly shared budgets
            limit: Maximum number of results

        Returns:
            List of campaign budgets
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    campaign_budget.resource_name,
                    campaign_budget.id,
                    campaign_budget.name,
                    campaign_budget.amount_micros,
                    campaign_budget.status,
                    campaign_budget.delivery_method,
                    campaign_budget.explicitly_shared,
                    campaign_budget.reference_count,
                    campaign_budget.period
                FROM campaign_budget
            """

            conditions = []
            if not include_removed:
                conditions.append("campaign_budget.status != 'REMOVED'")
            if explicitly_shared_only is not None:
                val = "true" if explicitly_shared_only else "false"
                conditions.append(f"campaign_budget.explicitly_shared = {val}")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY campaign_budget.id DESC LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            budgets = []
            for row in response:
                b = row.campaign_budget
                budgets.append(
                    {
                        "resource_name": b.resource_name,
                        "id": str(b.id),
                        "name": b.name,
                        "amount_micros": str(b.amount_micros),
                        "status": b.status.name if b.status else "UNKNOWN",
                        "delivery_method": b.delivery_method.name
                        if b.delivery_method
                        else "UNKNOWN",
                        "explicitly_shared": b.explicitly_shared,
                        "reference_count": b.reference_count,
                        "period": b.period.name if b.period else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(budgets)} campaign budgets",
            )

            return budgets

        except Exception as e:
            error_msg = f"Failed to list campaign budgets: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_campaign_budget(
        self,
        ctx: Context,
        customer_id: str,
        budget_id: str,
    ) -> Dict[str, Any]:
        """Remove a campaign budget.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            budget_id: The budget ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/campaignBudgets/{budget_id}"

            operation = CampaignBudgetOperation()
            operation.remove = resource_name

            request = MutateCampaignBudgetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateCampaignBudgetsResponse = (
                self.client.mutate_campaign_budgets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Removed campaign budget {budget_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove campaign budget: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_campaign_budget_tools(
    service: CampaignBudgetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for campaign budget service."""
    tools = []

    async def list_campaign_budgets(
        ctx: Context,
        customer_id: str,
        include_removed: bool = False,
        explicitly_shared_only: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign budgets for a customer account.

        Args:
            customer_id: The customer ID
            include_removed: Whether to include removed budgets
            explicitly_shared_only: If True, only return shared budgets
            limit: Maximum number of results

        Returns:
            List of campaign budgets with amounts and status
        """
        return await service.list_campaign_budgets(
            ctx=ctx,
            customer_id=customer_id,
            include_removed=include_removed,
            explicitly_shared_only=explicitly_shared_only,
            limit=limit,
        )

    async def remove_campaign_budget(
        ctx: Context,
        customer_id: str,
        budget_id: str,
    ) -> Dict[str, Any]:
        """Remove a campaign budget.

        Note: Only budgets not currently associated with any campaigns can be removed.

        Args:
            customer_id: The customer ID
            budget_id: The budget ID to remove

        Returns:
            Removal result
        """
        return await service.remove_campaign_budget(
            ctx=ctx,
            customer_id=customer_id,
            budget_id=budget_id,
        )

    tools.extend(
        [
            list_campaign_budgets,
            remove_campaign_budget,
        ]
    )
    return tools


def register_campaign_budget_tools(mcp: FastMCP[Any]) -> CampaignBudgetService:
    """Register campaign budget tools with the MCP server."""
    service = CampaignBudgetService()
    tools = create_campaign_budget_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
