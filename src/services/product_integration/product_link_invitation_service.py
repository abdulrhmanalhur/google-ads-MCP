"""Product link invitation service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.product_link_invitation_status import (
    ProductLinkInvitationStatusEnum,
)
from google.ads.googleads.v20.resources.types.product_link_invitation import (
    HotelCenterLinkInvitationIdentifier,
    MerchantCenterLinkInvitationIdentifier,
    ProductLinkInvitation,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.services.product_link_invitation_service import (
    ProductLinkInvitationServiceClient,
)
from google.ads.googleads.v20.services.types.product_link_invitation_service import (
    CreateProductLinkInvitationRequest,
    CreateProductLinkInvitationResponse,
    RemoveProductLinkInvitationRequest,
    RemoveProductLinkInvitationResponse,
    UpdateProductLinkInvitationRequest,
    UpdateProductLinkInvitationResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class ProductLinkInvitationService:
    """Service for managing product link invitations."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[ProductLinkInvitationServiceClient] = None

    @property
    def client(self) -> ProductLinkInvitationServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("ProductLinkInvitationService")
        assert self._client is not None
        return self._client

    async def create_merchant_center_invitation(
        self,
        ctx: Context,
        customer_id: str,
        merchant_center_id: int,
    ) -> Dict[str, Any]:
        """Create a Merchant Center product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            merchant_center_id: The Merchant Center ID to invite

        Returns:
            Created invitation details
        """
        try:
            customer_id = format_customer_id(customer_id)

            merchant_identifier = MerchantCenterLinkInvitationIdentifier()
            merchant_identifier.merchant_center_id = merchant_center_id

            invitation = ProductLinkInvitation()
            invitation.merchant_center = merchant_identifier

            request = CreateProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.product_link_invitation = invitation

            response: CreateProductLinkInvitationResponse = (
                self.client.create_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created Merchant Center invitation for {merchant_center_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create Merchant Center invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def create_hotel_center_invitation(
        self,
        ctx: Context,
        customer_id: str,
        hotel_center_id: int,
    ) -> Dict[str, Any]:
        """Create a Hotel Center product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            hotel_center_id: The Hotel Center ID to invite

        Returns:
            Created invitation details
        """
        try:
            customer_id = format_customer_id(customer_id)

            hotel_identifier = HotelCenterLinkInvitationIdentifier()
            hotel_identifier.hotel_center_id = hotel_center_id

            invitation = ProductLinkInvitation()
            invitation.hotel_center = hotel_identifier

            request = CreateProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.product_link_invitation = invitation

            response: CreateProductLinkInvitationResponse = (
                self.client.create_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created Hotel Center invitation for {hotel_center_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create Hotel Center invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_invitation_status(
        self,
        ctx: Context,
        customer_id: str,
        invitation_id: str,
        status: ProductLinkInvitationStatusEnum.ProductLinkInvitationStatus,
    ) -> Dict[str, Any]:
        """Update the status of a product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            invitation_id: The invitation ID
            status: New invitation status

        Returns:
            Updated invitation details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/productLinkInvitations/{invitation_id}"
            )

            request = UpdateProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name
            request.product_link_invitation_status = status

            response: UpdateProductLinkInvitationResponse = (
                self.client.update_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Updated invitation {invitation_id} status",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update invitation status: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_invitation(
        self,
        ctx: Context,
        customer_id: str,
        invitation_id: str,
    ) -> Dict[str, Any]:
        """Remove a product link invitation.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            invitation_id: The invitation ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/productLinkInvitations/{invitation_id}"
            )

            request = RemoveProductLinkInvitationRequest()
            request.customer_id = customer_id
            request.resource_name = resource_name

            response: RemoveProductLinkInvitationResponse = (
                self.client.remove_product_link_invitation(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Removed product link invitation {invitation_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove invitation: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_product_link_invitations(
        self,
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List product link invitations.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of product link invitations
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = f"""
                SELECT
                    product_link_invitation.resource_name,
                    product_link_invitation.product_link_invitation_id,
                    product_link_invitation.status,
                    product_link_invitation.type
                FROM product_link_invitation
                LIMIT {limit}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            invitations = []
            for row in response:
                inv = row.product_link_invitation
                invitations.append(
                    {
                        "resource_name": inv.resource_name,
                        "product_link_invitation_id": str(
                            inv.product_link_invitation_id
                        ),
                        "status": inv.status.name if inv.status else "UNKNOWN",
                        "type": inv.type_.name if inv.type_ else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(invitations)} product link invitations",
            )

            return invitations

        except Exception as e:
            error_msg = f"Failed to list product link invitations: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_product_link_invitation_tools(
    service: ProductLinkInvitationService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for product link invitation service."""
    tools = []

    async def create_merchant_center_invitation(
        ctx: Context,
        customer_id: str,
        merchant_center_id: int,
    ) -> Dict[str, Any]:
        """Create a Merchant Center product link invitation.

        Args:
            customer_id: The customer ID
            merchant_center_id: The Merchant Center account ID to invite

        Returns:
            Created invitation details
        """
        return await service.create_merchant_center_invitation(
            ctx=ctx,
            customer_id=customer_id,
            merchant_center_id=merchant_center_id,
        )

    async def create_hotel_center_invitation(
        ctx: Context,
        customer_id: str,
        hotel_center_id: int,
    ) -> Dict[str, Any]:
        """Create a Hotel Center product link invitation.

        Args:
            customer_id: The customer ID
            hotel_center_id: The Hotel Center account ID to invite

        Returns:
            Created invitation details
        """
        return await service.create_hotel_center_invitation(
            ctx=ctx,
            customer_id=customer_id,
            hotel_center_id=hotel_center_id,
        )

    async def update_product_link_invitation_status(
        ctx: Context,
        customer_id: str,
        invitation_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update the status of a product link invitation.

        Args:
            customer_id: The customer ID
            invitation_id: The invitation ID
            status: New status - PENDING_APPROVAL, APPROVED, DECLINED, EXPIRED, CANCELLED,
                INELIGIBLE

        Returns:
            Updated invitation details
        """
        status_enum = getattr(
            ProductLinkInvitationStatusEnum.ProductLinkInvitationStatus, status
        )
        return await service.update_invitation_status(
            ctx=ctx,
            customer_id=customer_id,
            invitation_id=invitation_id,
            status=status_enum,
        )

    async def remove_product_link_invitation(
        ctx: Context,
        customer_id: str,
        invitation_id: str,
    ) -> Dict[str, Any]:
        """Remove a product link invitation.

        Args:
            customer_id: The customer ID
            invitation_id: The invitation ID to remove

        Returns:
            Removal result
        """
        return await service.remove_invitation(
            ctx=ctx,
            customer_id=customer_id,
            invitation_id=invitation_id,
        )

    async def list_product_link_invitations(
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List product link invitations.

        Args:
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of product link invitations with their status and type
        """
        return await service.list_product_link_invitations(
            ctx=ctx,
            customer_id=customer_id,
            limit=limit,
        )

    tools.extend(
        [
            create_merchant_center_invitation,
            create_hotel_center_invitation,
            update_product_link_invitation_status,
            remove_product_link_invitation,
            list_product_link_invitations,
        ]
    )
    return tools


def register_product_link_invitation_tools(
    mcp: FastMCP[Any],
) -> ProductLinkInvitationService:
    """Register product link invitation tools with the MCP server."""
    service = ProductLinkInvitationService()
    tools = create_product_link_invitation_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
