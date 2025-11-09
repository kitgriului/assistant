"""Database models: User, Request, Patrol, Media.

This module defines the SQLAlchemy ORM models for the GuardBot application.
All models use declarative base and include proper indexing for performance.

Models:
    - User: System users (guests, guards, admins)
    - Request: Access requests and passes
    - Patrol: Legacy patrol records
    - PatrolEvent: Modern patrol session management
    - PatrolCheckpoint: Individual checkpoints within patrol
    - CheckpointPhoto: Photos attached to checkpoints
    - PatrolQuestion: Admin questions about patrols
    - PatrolAnswer: Guard answers to questions
    - Media: Generic media file storage
"""
from typing import Optional
from datetime import datetime as dt
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, 
    Boolean, Float, Index
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column

Base = declarative_base()


class User(Base):
    """Application user model.
    
    Represents all users in the system with role-based access control.
    Supports three roles: guest (default), guard, and admin.
    
    Attributes:
        id: Primary key
        telegram_id: Unique Telegram user ID (indexed)
        phone_number: Phone number from Telegram (optional, unique)
        role: User role (guest/guard/admin)
        name: Full name of the user
        is_blocked: Whether user is blocked from the system
        registered_at: Registration timestamp (UTC)
        last_activity: Last activity timestamp (UTC)
        patrol_events: Related patrol events (for guards)
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_telegram_id", "telegram_id"),
        Index("idx_users_role", "role"),
        Index("idx_users_phone", "phone_number"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    phone_number = Column(String(32), unique=True, nullable=True)
    role = Column(String(32), default="guest", nullable=False)
    name = Column(String(255), nullable=True)
    
    # Account status
    is_blocked = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    registered_at = Column(DateTime, default=dt.utcnow, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    
    # Relationships
    patrol_events = relationship("PatrolEvent", back_populates="guard", lazy="select")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User(id={self.id}, tg={self.telegram_id}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    @property
    def is_guard(self) -> bool:
        """Check if user has guard role."""
        return self.role == "guard"
    
    @property
    def is_guest(self) -> bool:
        """Check if user has guest role."""
        return self.role == "guest"


class Request(Base):
    """Access request and pass model.
    
    Manages the full lifecycle of access requests from submission to usage.
    Supports both pedestrian and vehicle passes with QR code generation.
    
    Attributes:
        id: Primary key
        applicant_id: Foreign key to User who submitted request
        name: Name of person requesting access
        pass_type: Type of pass (pedestrian/vehicle)
        purpose: Purpose of visit
        datetime: Requested date/time of visit
        photo: Path to uploaded photo
        car_number: Vehicle registration number (for vehicle passes)
        status: Current status (pending/approved/rejected/used/expired)
        processed_by_id: Foreign key to User who processed request
        processed_at: Timestamp when processed
        rejection_reason: Reason for rejection (if rejected)
        valid_until: Expiration timestamp for approved passes
        created_at: Request creation timestamp
        qr_code: Unique QR code identifier for approved passes
    """
    __tablename__ = "requests"
    __table_args__ = (
        Index("idx_requests_applicant_id", "applicant_id"),
        Index("idx_requests_status", "status"),
        Index("idx_requests_qr_code", "qr_code"),
        Index("idx_requests_created_at", "created_at"),
        Index("idx_requests_valid_until", "valid_until"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Request data
    name = Column(String(255), nullable=False)
    pass_type = Column(String(32), default="pedestrian", nullable=False)  # pedestrian or vehicle
    purpose = Column(String(512), nullable=False)
    datetime = Column(String(64), nullable=True)
    photo = Column(String(1024), nullable=True)
    car_number = Column(String(64), nullable=True)  # Required for vehicle passes
    
    # Status tracking
    status = Column(String(32), default="pending", nullable=False)
    
    # Processing information
    processed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Rejection details
    rejection_reason = Column(Text, nullable=True)
    
    # Pass validity
    valid_until = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    qr_code = Column(String(256), unique=True, nullable=True)
    
    # Relationships
    applicant = relationship("User", foreign_keys=[applicant_id], lazy="joined")
    processed_by = relationship("User", foreign_keys=[processed_by_id], lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Request(id={self.id}, status={self.status}, name={self.name!r})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if request is pending approval."""
        return self.status == "pending"
    
    @property
    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == "approved"
    
    @property
    def is_active(self) -> bool:
        """Check if pass is active (approved and not expired)."""
        if self.status != "approved":
            return False
        if self.valid_until and dt.utcnow() > self.valid_until:
            return False
        return True


class Patrol(Base):
    """Legacy patrol record model.
    
    Simple patrol logging system (deprecated in favor of PatrolEvent).
    Kept for backward compatibility with existing data.
    
    Attributes:
        id: Primary key
        timestamp: When patrol was recorded
        code: Optional code/identifier
        photo: Path to patrol photo
    """
    __tablename__ = "patrols"
    __table_args__ = (
        Index("idx_patrols_timestamp", "timestamp"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=dt.utcnow, nullable=False)
    code = Column(String(256), nullable=True)
    photo = Column(String(1024), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, dt) else self.timestamp
        return f"<Patrol(id={self.id}, ts={ts})>"


class PatrolEvent(Base):
    """Patrol event model - represents a complete patrol session.
    
    Modern patrol tracking system that manages the full lifecycle of a
    patrol round from start to completion, including checkpoints and Q&A.
    
    Attributes:
        id: Primary key
        guard_id: Foreign key to User performing patrol
        started_at: When patrol session began
        completed_at: When patrol session ended (None if in progress)
        status: Current status (in_progress/completed/cancelled)
        notes: Optional notes about the patrol
        guard: Related User object
        checkpoints: List of checkpoints visited
        questions: List of admin questions about this patrol
    """
    __tablename__ = "patrol_events"
    __table_args__ = (
        Index("idx_patrol_events_guard_id", "guard_id"),
        Index("idx_patrol_events_status", "status"),
        Index("idx_patrol_events_started_at", "started_at"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guard_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Time tracking
    started_at = Column(DateTime, default=dt.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(32), default="in_progress", nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Relationships
    guard = relationship("User", back_populates="patrol_events", lazy="joined")
    checkpoints = relationship(
        "PatrolCheckpoint", 
        back_populates="event", 
        cascade="all, delete-orphan",
        lazy="select",
        order_by="PatrolCheckpoint.checkpoint_number"
    )
    questions = relationship(
        "PatrolQuestion", 
        back_populates="event", 
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PatrolEvent(id={self.id}, guard_id={self.guard_id}, status={self.status})>"
    
    @property
    def is_in_progress(self) -> bool:
        """Check if patrol is currently in progress."""
        return self.status == "in_progress"
    
    @property
    def is_completed(self) -> bool:
        """Check if patrol is completed."""
        return self.status == "completed"
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate patrol duration in minutes."""
        if not self.completed_at:
            return None
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() / 60)


class PatrolCheckpoint(Base):
    """Patrol checkpoint model.
    
    Represents a single checkpoint visited during a patrol event.
    Can include location, photos, and notes.
    
    Attributes:
        id: Primary key
        event_id: Foreign key to PatrolEvent
        checkpoint_number: Sequential number of checkpoint in patrol
        latitude: GPS latitude (optional)
        longitude: GPS longitude (optional)
        timestamp: When checkpoint was recorded
        notes: Optional notes about this checkpoint
        event: Related PatrolEvent object
        photos: List of photos taken at this checkpoint
    """
    __tablename__ = "patrol_checkpoints"
    __table_args__ = (
        Index("idx_patrol_checkpoints_event_id", "event_id"),
        Index("idx_patrol_checkpoints_timestamp", "timestamp"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("patrol_events.id", ondelete="CASCADE"), nullable=False)
    
    # Checkpoint information
    checkpoint_number = Column(Integer, nullable=False)
    
    # Location (optional)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=dt.utcnow, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    event = relationship("PatrolEvent", back_populates="checkpoints")
    photos = relationship(
        "CheckpointPhoto", 
        back_populates="checkpoint", 
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PatrolCheckpoint(id={self.id}, event_id={self.event_id}, "
            f"n={self.checkpoint_number})>"
        )
    
    @property
    def has_location(self) -> bool:
        """Check if checkpoint has GPS coordinates."""
        return self.latitude is not None and self.longitude is not None


class CheckpointPhoto(Base):
    """Photo attached to patrol checkpoint.
    
    Stores individual photos taken at patrol checkpoints.
    
    Attributes:
        id: Primary key
        checkpoint_id: Foreign key to PatrolCheckpoint
        photo_path: File system path to photo
        uploaded_at: When photo was uploaded
        description: Optional photo description
        checkpoint: Related PatrolCheckpoint object
    """
    __tablename__ = "checkpoint_photos"
    __table_args__ = (
        Index("idx_checkpoint_photos_checkpoint_id", "checkpoint_id"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(Integer, ForeignKey("patrol_checkpoints.id", ondelete="CASCADE"), nullable=False)
    
    # Photo information
    photo_path = Column(String(1024), nullable=False)
    
    # Metadata
    uploaded_at = Column(DateTime, default=dt.utcnow, nullable=False)
    description = Column(String(512), nullable=True)
    
    # Relationship
    checkpoint = relationship("PatrolCheckpoint", back_populates="photos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CheckpointPhoto(id={self.id}, checkpoint_id={self.checkpoint_id})>"


class PatrolQuestion(Base):
    """Admin question about patrol event.
    
    Allows administrators to ask questions about patrol events
    which guards must answer.
    
    Attributes:
        id: Primary key
        event_id: Foreign key to PatrolEvent
        admin_id: Foreign key to User who asked question
        question_text: The question text
        asked_at: When question was asked
        is_answered: Whether question has been answered
        event: Related PatrolEvent object
        admin: Related User object (admin)
        answer: Related PatrolAnswer object (if answered)
    """
    __tablename__ = "patrol_questions"
    __table_args__ = (
        Index("idx_patrol_questions_event_id", "event_id"),
        Index("idx_patrol_questions_is_answered", "is_answered"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("patrol_events.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Question details
    question_text = Column(Text, nullable=False)
    asked_at = Column(DateTime, default=dt.utcnow, nullable=False)
    
    # Status
    is_answered = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    event = relationship("PatrolEvent", back_populates="questions")
    admin = relationship("User", foreign_keys=[admin_id], lazy="joined")
    answer = relationship(
        "PatrolAnswer", 
        back_populates="question", 
        uselist=False,
        lazy="joined"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PatrolQuestion(id={self.id}, event_id={self.event_id}, "
            f"admin_id={self.admin_id}, answered={self.is_answered})>"
        )


class PatrolAnswer(Base):
    """Guard's answer to admin question.
    
    Stores guard responses to admin questions about patrol events.
    
    Attributes:
        id: Primary key
        question_id: Foreign key to PatrolQuestion
        answer_text: The answer text
        answered_at: When answer was provided
        question: Related PatrolQuestion object
    """
    __tablename__ = "patrol_answers"
    __table_args__ = (
        Index("idx_patrol_answers_question_id", "question_id"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("patrol_questions.id", ondelete="CASCADE"), nullable=False)
    
    # Answer details
    answer_text = Column(Text, nullable=False)
    answered_at = Column(DateTime, default=dt.utcnow, nullable=False)
    
    # Relationship
    question = relationship("PatrolQuestion", back_populates="answer")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PatrolAnswer(id={self.id}, question_id={self.question_id})>"


class Media(Base):
    """Generic media file storage.
    
    Stores metadata for uploaded media files.
    
    Attributes:
        id: Primary key
        path: File system path to media file
        uploaded_at: When file was uploaded
    """
    __tablename__ = "media"
    __table_args__ = (
        Index("idx_media_uploaded_at", "uploaded_at"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime, default=dt.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Media(id={self.id}, path={self.path!r})>"
