"""Repository interface for consent data access."""

from abc import ABC, abstractmethod
from uuid import UUID

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.value_objects import ContactInfo, ConsentStatus


class IConsentRepository(ABC):
    """
    Interface for consent data access.
    
    Implement this interface to use any database backend.
    The domain layer depends only on this interface, not concrete implementations.
    """

    @abstractmethod
    async def create(self, request: ConsentRequest) -> ConsentRequest:
        """
        Create a new consent request.
        
        Args:
            request: The consent request to create.
            
        Returns:
            The created consent request with generated ID.
            
        Raises:
            DuplicateRequestError: If a request already exists for this
                requester+target+scope combination.
        """
        pass

    @abstractmethod
    async def get_by_id(self, request_id: UUID) -> ConsentRequest | None:
        """
        Get a consent request by ID.
        
        Args:
            request_id: The unique identifier of the request.
            
        Returns:
            The consent request if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_active_consent(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str | None = None,
    ) -> ConsentRequest | None:
        """
        Get active (granted, unexpired) consent between requester and target.
        
        Args:
            requester: The requester's contact information.
            target: The target's contact information.
            scope: Optional scope to filter by. If None, returns any active consent.
            
        Returns:
            The active consent request if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_pending_request(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str,
    ) -> ConsentRequest | None:
        """
        Get a pending consent request for the given requester+target+scope.
        
        Args:
            requester: The requester's contact information.
            target: The target's contact information.
            scope: The scope of the request.
            
        Returns:
            The pending request if found, None otherwise.
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        request_id: UUID,
        status: ConsentStatus,
    ) -> ConsentRequest:
        """
        Update the status of a consent request.
        
        Args:
            request_id: The ID of the request to update.
            status: The new status.
            
        Returns:
            The updated consent request.
            
        Raises:
            RequestNotFoundError: If the request doesn't exist.
        """
        pass

    @abstractmethod
    async def find_by_target(
        self,
        target: ContactInfo,
        status: ConsentStatus | None = None,
    ) -> list[ConsentRequest]:
        """
        Find all consent requests for a target.
        
        Args:
            target: The target's contact information.
            status: Optional status to filter by.
            
        Returns:
            List of matching consent requests.
        """
        pass

    @abstractmethod
    async def find_by_requester(
        self,
        requester: ContactInfo,
        status: ConsentStatus | None = None,
    ) -> list[ConsentRequest]:
        """
        Find all consent requests from a requester.
        
        Args:
            requester: The requester's contact information.
            status: Optional status to filter by.
            
        Returns:
            List of matching consent requests.
        """
        pass

    @abstractmethod
    async def expire_old_requests(self) -> int:
        """
        Mark expired requests as EXPIRED status.
        
        This should be called periodically to update status of
        requests past their expires_at time.
        
        Returns:
            Number of requests marked as expired.
        """
        pass


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class DuplicateRequestError(RepositoryError):
    """Raised when trying to create a duplicate consent request."""

    pass


class RequestNotFoundError(RepositoryError):
    """Raised when a consent request is not found."""

    pass
