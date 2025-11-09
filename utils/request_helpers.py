"""Request management utilities.

Helper functions for creating, updating, and querying access requests.
Centralizes request logic to reduce duplication across handlers.
"""
from typing import Optional, List
import datetime
import logging
import secrets

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from database.session import get_session
from database.models import Request, User
from utils.constants import RequestStatus, PassType
from bot.config import settings


logger = logging.getLogger(__name__)


def generate_qr_code() -> str:
    """Generate unique QR code identifier.
    
    Creates a cryptographically secure random code for pass QR codes.
    
    Returns:
        32-character hexadecimal QR code string
        
    Example:
        qr_code = generate_qr_code()  # "a3f2c9e1..."
    """
    return secrets.token_hex(16)


async def create_request(
    applicant_id: int,
    name: str,
    purpose: str,
    pass_type: str = PassType.PEDESTRIAN.value,
    datetime_str: Optional[str] = None,
    photo: Optional[str] = None,
    car_number: Optional[str] = None,
) -> Request:
    """Create new access request.
    
    Args:
        applicant_id: ID of user submitting request
        name: Name of person requesting access
        purpose: Purpose of visit
        pass_type: Type of pass (pedestrian/vehicle)
        datetime_str: Requested date/time of visit
        photo: Path to uploaded photo
        car_number: Vehicle registration (required for vehicle passes)
        
    Returns:
        Created Request object
        
    Raises:
        ValueError: If vehicle pass requested without car_number
        
    Example:
        request = await create_request(
            applicant_id=user.id,
            name="John Doe",
            purpose="Meeting with director",
            pass_type=PassType.PEDESTRIAN.value,
        )
    """
    if pass_type == PassType.VEHICLE.value and not car_number:
        raise ValueError("Car number is required for vehicle passes")
    
    async with get_session() as session:
        request = Request(
            applicant_id=applicant_id,
            name=name,
            purpose=purpose,
            pass_type=pass_type,
            datetime=datetime_str,
            photo=photo,
            car_number=car_number,
            status=RequestStatus.PENDING.value,
        )
        
        session.add(request)
        await session.commit()
        await session.refresh(request)
        
        logger.info(
            f"Created request: id={request.id}, applicant={applicant_id}, "
            f"type={pass_type}, name={name}"
        )
        return request


async def approve_request(
    request_id: int,
    processed_by_id: int,
    validity_days: Optional[int] = None,
) -> Optional[Request]:
    """Approve access request and generate QR code.
    
    Args:
        request_id: ID of request to approve
        processed_by_id: ID of user approving request
        validity_days: Number of days pass is valid (uses config default if None)
        
    Returns:
        Updated Request object, or None if not found
        
    Example:
        request = await approve_request(
            request_id=123,
            processed_by_id=admin.id,
            validity_days=3,
        )
        if request:
            # Send QR code to applicant
    """
    if validity_days is None:
        validity_days = settings.pass_validity_days
    
    async with get_session() as session:
        result = await session.execute(
            select(Request).where(Request.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            logger.warning(f"Cannot approve: request {request_id} not found")
            return None
        
        # Update request status
        request.status = RequestStatus.APPROVED.value
        request.processed_by_id = processed_by_id
        request.processed_at = datetime.datetime.utcnow()
        request.qr_code = generate_qr_code()
        request.valid_until = datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
        
        await session.commit()
        await session.refresh(request)
        
        logger.info(
            f"Approved request: id={request.id}, qr_code={request.qr_code}, "
            f"valid_until={request.valid_until}"
        )
        return request


async def reject_request(
    request_id: int,
    processed_by_id: int,
    reason: str,
) -> Optional[Request]:
    """Reject access request.
    
    Args:
        request_id: ID of request to reject
        processed_by_id: ID of user rejecting request
        reason: Reason for rejection
        
    Returns:
        Updated Request object, or None if not found
        
    Example:
        request = await reject_request(
            request_id=123,
            processed_by_id=admin.id,
            reason="Incomplete documentation",
        )
    """
    async with get_session() as session:
        result = await session.execute(
            select(Request).where(Request.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            logger.warning(f"Cannot reject: request {request_id} not found")
            return None
        
        # Update request status
        request.status = RequestStatus.REJECTED.value
        request.processed_by_id = processed_by_id
        request.processed_at = datetime.datetime.utcnow()
        request.rejection_reason = reason
        
        await session.commit()
        await session.refresh(request)
        
        logger.info(f"Rejected request: id={request.id}, reason={reason}")
        return request


async def get_pending_requests() -> List[Request]:
    """Get all pending requests.
    
    Returns:
        List of pending Request objects, ordered by creation date (oldest first)
        
    Example:
        pending = await get_pending_requests()
        for request in pending:
            # Process each pending request
    """
    async with get_session() as session:
        result = await session.execute(
            select(Request)
            .where(Request.status == RequestStatus.PENDING.value)
            .order_by(Request.created_at.asc())
        )
        return list(result.scalars().all())


async def get_active_passes() -> List[Request]:
    """Get all active (approved and valid) passes.
    
    Returns:
        List of active Request objects with valid passes
        
    Example:
        active = await get_active_passes()
        for pass_request in active:
            # Show active pass
    """
    now = datetime.datetime.utcnow()
    
    async with get_session() as session:
        result = await session.execute(
            select(Request)
            .where(
                and_(
                    Request.status == RequestStatus.APPROVED.value,
                    or_(
                        Request.valid_until.is_(None),
                        Request.valid_until > now
                    )
                )
            )
            .order_by(Request.valid_until.asc())
        )
        return list(result.scalars().all())


async def get_request_by_qr(qr_code: str) -> Optional[Request]:
    """Find request by QR code.
    
    Args:
        qr_code: QR code identifier to search for
        
    Returns:
        Request object if found, None otherwise
        
    Example:
        request = await get_request_by_qr(scanned_code)
        if request and request.is_active:
            # Allow entry
    """
    async with get_session() as session:
        result = await session.execute(
            select(Request).where(Request.qr_code == qr_code)
        )
        return result.scalar_one_or_none()


async def mark_request_used(request_id: int) -> Optional[Request]:
    """Mark request as used (pass scanned at entry).
    
    Args:
        request_id: ID of request to mark as used
        
    Returns:
        Updated Request object, or None if not found
        
    Example:
        request = await mark_request_used(request.id)
        if request:
            await message.answer("Pass marked as used")
    """
    async with get_session() as session:
        result = await session.execute(
            select(Request).where(Request.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            logger.warning(f"Cannot mark used: request {request_id} not found")
            return None
        
        request.status = RequestStatus.USED.value
        await session.commit()
        await session.refresh(request)
        
        logger.info(f"Marked request as used: id={request.id}")
        return request


async def expire_old_passes() -> int:
    """Mark expired passes as expired.
    
    Should be run periodically (e.g., daily cron job) to clean up old passes.
    
    Returns:
        Number of passes that were marked as expired
        
    Example:
        expired_count = await expire_old_passes()
        logger.info(f"Expired {expired_count} passes")
    """
    now = datetime.datetime.utcnow()
    
    async with get_session() as session:
        result = await session.execute(
            select(Request)
            .where(
                and_(
                    Request.status == RequestStatus.APPROVED.value,
                    Request.valid_until.isnot(None),
                    Request.valid_until < now
                )
            )
        )
        expired_requests = result.scalars().all()
        
        count = 0
        for request in expired_requests:
            request.status = RequestStatus.EXPIRED.value
            count += 1
        
        await session.commit()
        
        logger.info(f"Expired {count} passes")
        return count


async def get_user_requests(user_id: int, limit: int = 10) -> List[Request]:
    """Get recent requests for a specific user.
    
    Args:
        user_id: Database ID of user
        limit: Maximum number of requests to return
        
    Returns:
        List of Request objects ordered by creation date (newest first)
        
    Example:
        my_requests = await get_user_requests(user.id, limit=5)
        for request in my_requests:
            # Show user their request history
    """
    async with get_session() as session:
        result = await session.execute(
            select(Request)
            .where(Request.applicant_id == user_id)
            .order_by(Request.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
