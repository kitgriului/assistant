"""Centralized constants and enums for roles and request statuses.

Using string-valued Enums minimizes typos and improves readability while
preserving existing database values (which are plain strings).
"""
from enum import Enum


class Role(str, Enum):
    GUEST = "guest"
    GUARD = "guard"
    ADMIN = "admin"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    USED = "used"
    EXPIRED = "expired"


class PassType(str, Enum):
    PEDESTRIAN = "pedestrian"
    VEHICLE = "vehicle"

