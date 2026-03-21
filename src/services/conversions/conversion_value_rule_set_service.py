"""Conversion value rule set service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.value_rule_set_attachment_type import (
    ValueRuleSetAttachmentTypeEnum,
)
from google.ads.googleads.v20.enums.types.value_rule_set_dimension import (
    ValueRuleSetDimensionEnum,
)
from google.ads.googleads.v20.resources.types.conversion_value_rule_set import (
    ConversionValueRuleSet,
)
from google.ads.googleads.v20.services.services.conversion_value_rule_set_service import (
    ConversionValueRuleSetServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.conversion_value_rule_set_service import (
    ConversionValueRuleSetOperation,
    MutateConversionValueRuleSetsRequest,
    MutateConversionValueRuleSetsResponse,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class ConversionValueRuleSetService:
    """Service for managing conversion value rule sets."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[ConversionValueRuleSetServiceClient] = None

    @property
    def client(self) -> ConversionValueRuleSetServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ConversionValueRuleSetService"
            )
        assert self._client is not None
        return self._client

    async def create_conversion_value_rule_set(
        self,
        ctx: Context,
        customer_id: str,
        dimensions: List[ValueRuleSetDimensionEnum.ValueRuleSetDimension],
        attachment_type: ValueRuleSetAttachmentTypeEnum.ValueRuleSetAttachmentType,
        conversion_value_rules: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            dimensions: List of dimensions for value rule conditions
            attachment_type: Where the rule set is attached (CUSTOMER or CAMPAIGN)
            conversion_value_rules: Optional list of conversion value rule resource names
            campaign_id: Optional campaign ID (when attachment_type is CAMPAIGN)

        Returns:
            Created rule set details
        """
        try:
            customer_id = format_customer_id(customer_id)

            rule_set = ConversionValueRuleSet()
            rule_set.dimensions.extend(dimensions)
            rule_set.attachment_type = attachment_type

            if conversion_value_rules:
                rule_set.conversion_value_rules.extend(conversion_value_rules)

            if campaign_id:
                rule_set.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"

            operation = ConversionValueRuleSetOperation()
            operation.create = rule_set

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateConversionValueRuleSetsResponse = (
                self.client.mutate_conversion_value_rule_sets(request=request)
            )

            await ctx.log(
                level="info",
                message="Created conversion value rule set",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_conversion_value_rule_set(
        self,
        ctx: Context,
        customer_id: str,
        conversion_value_rule_set_id: str,
        conversion_value_rules: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update a conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            conversion_value_rule_set_id: The rule set ID
            conversion_value_rules: Optional new list of rule resource names

        Returns:
            Updated rule set details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/conversionValueRuleSets/{conversion_value_rule_set_id}"

            rule_set = ConversionValueRuleSet()
            rule_set.resource_name = resource_name

            update_mask_paths = []

            if conversion_value_rules is not None:
                rule_set.conversion_value_rules.extend(conversion_value_rules)
                update_mask_paths.append("conversion_value_rules")

            operation = ConversionValueRuleSetOperation()
            operation.update = rule_set
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=update_mask_paths)
            )

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_conversion_value_rule_sets(request=request)

            await ctx.log(
                level="info",
                message=f"Updated conversion value rule set {conversion_value_rule_set_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_conversion_value_rule_set(
        self,
        ctx: Context,
        customer_id: str,
        conversion_value_rule_set_id: str,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            conversion_value_rule_set_id: The rule set ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/conversionValueRuleSets/{conversion_value_rule_set_id}"

            operation = ConversionValueRuleSetOperation()
            operation.remove = resource_name

            request = MutateConversionValueRuleSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_conversion_value_rule_sets(request=request)

            await ctx.log(
                level="info",
                message=f"Removed conversion value rule set {conversion_value_rule_set_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove conversion value rule set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_conversion_value_rule_sets(
        self,
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List conversion value rule sets.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of conversion value rule sets
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    conversion_value_rule_set.resource_name,
                    conversion_value_rule_set.id,
                    conversion_value_rule_set.conversion_value_rules,
                    conversion_value_rule_set.dimensions,
                    conversion_value_rule_set.attachment_type,
                    conversion_value_rule_set.campaign,
                    conversion_value_rule_set.status
                FROM conversion_value_rule_set
            """

            conditions = ["conversion_value_rule_set.status != 'REMOVED'"]
            if campaign_id:
                campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"
                conditions.append(
                    f"conversion_value_rule_set.campaign = '{campaign_resource}'"
                )

            query += " WHERE " + " AND ".join(conditions)
            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            rule_sets = []
            for row in response:
                rs = row.conversion_value_rule_set
                rule_sets.append(
                    {
                        "resource_name": rs.resource_name,
                        "id": str(rs.id),
                        "conversion_value_rules": list(rs.conversion_value_rules),
                        "dimensions": [d.name for d in rs.dimensions],
                        "attachment_type": rs.attachment_type.name
                        if rs.attachment_type
                        else "UNKNOWN",
                        "campaign": rs.campaign,
                        "status": rs.status.name if rs.status else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(rule_sets)} conversion value rule sets",
            )

            return rule_sets

        except Exception as e:
            error_msg = f"Failed to list conversion value rule sets: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_conversion_value_rule_set_tools(
    service: ConversionValueRuleSetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for conversion value rule set service."""
    tools = []

    async def create_conversion_value_rule_set(
        ctx: Context,
        customer_id: str,
        dimensions: List[str],
        attachment_type: str = "CUSTOMER",
        conversion_value_rules: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a conversion value rule set.

        Args:
            customer_id: The customer ID
            dimensions: List of dimension types - GEO_LOCATION, DEVICE, AUDIENCE, NO_CONDITION
            attachment_type: Where attached - CUSTOMER or CAMPAIGN
            conversion_value_rules: Optional list of conversion value rule resource names
            campaign_id: Optional campaign ID (required when attachment_type is CAMPAIGN)

        Returns:
            Created rule set details
        """
        dims = [
            getattr(ValueRuleSetDimensionEnum.ValueRuleSetDimension, d)
            for d in dimensions
        ]
        attach_type = getattr(
            ValueRuleSetAttachmentTypeEnum.ValueRuleSetAttachmentType, attachment_type
        )
        return await service.create_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            dimensions=dims,
            attachment_type=attach_type,
            conversion_value_rules=conversion_value_rules,
            campaign_id=campaign_id,
        )

    async def update_conversion_value_rule_set(
        ctx: Context,
        customer_id: str,
        conversion_value_rule_set_id: str,
        conversion_value_rules: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update a conversion value rule set.

        Args:
            customer_id: The customer ID
            conversion_value_rule_set_id: The rule set ID
            conversion_value_rules: Optional new list of rule resource names

        Returns:
            Updated rule set details
        """
        return await service.update_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            conversion_value_rule_set_id=conversion_value_rule_set_id,
            conversion_value_rules=conversion_value_rules,
        )

    async def remove_conversion_value_rule_set(
        ctx: Context,
        customer_id: str,
        conversion_value_rule_set_id: str,
    ) -> Dict[str, Any]:
        """Remove a conversion value rule set.

        Args:
            customer_id: The customer ID
            conversion_value_rule_set_id: The rule set ID to remove

        Returns:
            Removal result
        """
        return await service.remove_conversion_value_rule_set(
            ctx=ctx,
            customer_id=customer_id,
            conversion_value_rule_set_id=conversion_value_rule_set_id,
        )

    async def list_conversion_value_rule_sets(
        ctx: Context,
        customer_id: str,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List conversion value rule sets.

        Args:
            customer_id: The customer ID
            campaign_id: Optional campaign ID to filter by
            limit: Maximum number of results

        Returns:
            List of conversion value rule sets
        """
        return await service.list_conversion_value_rule_sets(
            ctx=ctx,
            customer_id=customer_id,
            campaign_id=campaign_id,
            limit=limit,
        )

    tools.extend(
        [
            create_conversion_value_rule_set,
            update_conversion_value_rule_set,
            remove_conversion_value_rule_set,
            list_conversion_value_rule_sets,
        ]
    )
    return tools


def register_conversion_value_rule_set_tools(
    mcp: FastMCP[Any],
) -> ConversionValueRuleSetService:
    """Register conversion value rule set tools with the MCP server."""
    service = ConversionValueRuleSetService()
    tools = create_conversion_value_rule_set_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
