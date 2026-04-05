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


try:
    from rest_framework.permissions import BasePermission
except ImportError:  # pragma: no cover - optional dependency
    BasePermission = object  # type: ignore[misc, assignment]


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
