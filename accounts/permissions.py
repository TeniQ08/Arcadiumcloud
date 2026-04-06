"""
Role helpers for views and (optionally) DRF permission classes.

Wire `IsAdmin`, `IsCashier`, `IsAttendant` to Django REST Framework when installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import AnonymousUser

from .models import User

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def _is_authenticated_staff(user: AbstractBaseUser | AnonymousUser) -> bool:
    return bool(user.is_authenticated and isinstance(user, User))


def is_admin(user: AbstractBaseUser | AnonymousUser) -> bool:
    return _is_authenticated_staff(user) and user.role == User.Role.ADMIN


def is_cashier(user: AbstractBaseUser | AnonymousUser) -> bool:
    return _is_authenticated_staff(user) and user.role == User.Role.CASHIER


def is_attendant(user: AbstractBaseUser | AnonymousUser) -> bool:
    return _is_authenticated_staff(user) and user.role == User.Role.ATTENDANT


def is_cashier_or_admin(user: AbstractBaseUser | AnonymousUser) -> bool:
    return _is_authenticated_staff(user) and user.role in (
        User.Role.CASHIER,
        User.Role.ADMIN,
    )


def is_staff_role(user: AbstractBaseUser | AnonymousUser) -> bool:
    """Admin, cashier, or attendant (Arcadium control panel roles)."""
    return _is_authenticated_staff(user) and user.role in (
        User.Role.ADMIN,
        User.Role.CASHIER,
        User.Role.ATTENDANT,
    )


try:
    from rest_framework.permissions import BasePermission, IsAuthenticated
except ImportError:  # pragma: no cover - optional dependency
    BasePermission = object  # type: ignore[misc, assignment]
    IsAuthenticated = object  # type: ignore[misc, assignment]


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_admin(request.user)


class IsCashier(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_cashier(request.user)


class IsAttendant(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_attendant(request.user)


class IsCashierOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_cashier_or_admin(request.user)


class IsStaffRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_staff_role(request.user)


# Staff JSON API: authenticated user with admin, cashier, or attendant role.
STAFF_API_PERMISSIONS = [IsAuthenticated, IsStaffRole]
