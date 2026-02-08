"""PostgreSQL implementation of the consent repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.repository import (
    DuplicateRequestError,
    IConsentRepository,
    RequestNotFoundError,
)
from consent_mcp.domain.value_objects import ConsentStatus, ContactInfo, ContactType
from consent_mcp.infrastructure.database.models import ConsentRequestModel


class PostgresConsentRepository(IConsentRepository):
    """PostgreSQL implementation of the consent repository."""

    def __init__(self, session: AsyncSession):
        """Initialize with an async session."""
        self._session = session

    def _model_to_entity(self, model: ConsentRequestModel) -> ConsentRequest:
        """Convert ORM model to domain entity."""
        return ConsentRequest(
            id=model.id,
            requester=ContactInfo(
                contact_type=ContactType(model.requester_contact_type),
                contact_value=model.requester_contact_value,
                name=model.requester_name,
            ),
            target=ContactInfo(
                contact_type=ContactType(model.target_contact_type),
                contact_value=model.target_contact_value,
                name=model.target_name,
            ),
            scope=model.scope,
            status=ConsentStatus(model.status),
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            responded_at=model.responded_at,
        )

    def _entity_to_model(self, entity: ConsentRequest) -> ConsentRequestModel:
        """Convert domain entity to ORM model."""
        return ConsentRequestModel(
            id=entity.id,
            requester_contact_type=entity.requester.contact_type.value,
            requester_contact_value=entity.requester.contact_value,
            requester_name=entity.requester.name or "",
            target_contact_type=entity.target.contact_type.value,
            target_contact_value=entity.target.contact_value,
            target_name=entity.target.name,
            scope=entity.scope,
            status=entity.status.value,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            responded_at=entity.responded_at,
        )

    async def create(self, request: ConsentRequest) -> ConsentRequest:
        """Create a new consent request."""
        model = self._entity_to_model(request)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise DuplicateRequestError(
                f"Consent request already exists for this requester+target+scope: {e}"
            ) from e
        return self._model_to_entity(model)

    async def get_by_id(self, request_id: UUID) -> ConsentRequest | None:
        """Get a consent request by ID."""
        result = await self._session.execute(
            select(ConsentRequestModel).where(ConsentRequestModel.id == request_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_active_consent(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str | None = None,
    ) -> ConsentRequest | None:
        """Get active (granted, unexpired) consent."""
        now = datetime.utcnow()
        conditions = [
            ConsentRequestModel.requester_contact_type == requester.contact_type.value,
            ConsentRequestModel.requester_contact_value == requester.contact_value,
            ConsentRequestModel.target_contact_type == target.contact_type.value,
            ConsentRequestModel.target_contact_value == target.contact_value,
            ConsentRequestModel.status == ConsentStatus.GRANTED.value,
            ConsentRequestModel.expires_at > now,
        ]
        if scope:
            conditions.append(ConsentRequestModel.scope == scope)

        result = await self._session.execute(select(ConsentRequestModel).where(and_(*conditions)))
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_pending_request(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str,
    ) -> ConsentRequest | None:
        """Get a pending consent request."""
        result = await self._session.execute(
            select(ConsentRequestModel).where(
                and_(
                    ConsentRequestModel.requester_contact_type == requester.contact_type.value,
                    ConsentRequestModel.requester_contact_value == requester.contact_value,
                    ConsentRequestModel.target_contact_type == target.contact_type.value,
                    ConsentRequestModel.target_contact_value == target.contact_value,
                    ConsentRequestModel.scope == scope,
                    ConsentRequestModel.status == ConsentStatus.PENDING.value,
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update_status(
        self,
        request_id: UUID,
        status: ConsentStatus,
    ) -> ConsentRequest:
        """Update the status of a consent request."""
        now = datetime.utcnow()
        result = await self._session.execute(
            update(ConsentRequestModel)
            .where(ConsentRequestModel.id == request_id)
            .values(
                status=status.value,
                updated_at=now,
                responded_at=now
                if status in (ConsentStatus.GRANTED, ConsentStatus.REVOKED)
                else None,
            )
            .returning(ConsentRequestModel)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise RequestNotFoundError(f"Consent request not found: {request_id}")
        return self._model_to_entity(model)

    async def find_by_target(
        self,
        target: ContactInfo,
        status: ConsentStatus | None = None,
    ) -> list[ConsentRequest]:
        """Find all consent requests for a target."""
        conditions = [
            ConsentRequestModel.target_contact_type == target.contact_type.value,
            ConsentRequestModel.target_contact_value == target.contact_value,
        ]
        if status:
            conditions.append(ConsentRequestModel.status == status.value)

        result = await self._session.execute(select(ConsentRequestModel).where(and_(*conditions)))
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def find_by_requester(
        self,
        requester: ContactInfo,
        status: ConsentStatus | None = None,
    ) -> list[ConsentRequest]:
        """Find all consent requests from a requester."""
        conditions = [
            ConsentRequestModel.requester_contact_type == requester.contact_type.value,
            ConsentRequestModel.requester_contact_value == requester.contact_value,
        ]
        if status:
            conditions.append(ConsentRequestModel.status == status.value)

        result = await self._session.execute(select(ConsentRequestModel).where(and_(*conditions)))
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def expire_old_requests(self) -> int:
        """Mark expired requests as EXPIRED status."""
        now = datetime.utcnow()
        result = await self._session.execute(
            update(ConsentRequestModel)
            .where(
                and_(
                    ConsentRequestModel.status.in_(
                        [
                            ConsentStatus.PENDING.value,
                            ConsentStatus.GRANTED.value,
                        ]
                    ),
                    ConsentRequestModel.expires_at <= now,
                )
            )
            .values(
                status=ConsentStatus.EXPIRED.value,
                updated_at=now,
            )
        )
        return result.rowcount
