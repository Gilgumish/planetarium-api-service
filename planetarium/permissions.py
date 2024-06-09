from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )


class IsAdminOrIsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Admin users can view and edit any reservation.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read-only methods for any request
        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user or request.user.is_staff
