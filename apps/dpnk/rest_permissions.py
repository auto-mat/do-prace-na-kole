from rest_framework import permissions


class IsOwnerOrSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if (
            request.method in permissions.SAFE_METHODS
            and "register-challenge" not in request.build_absolute_uri()
        ):
            return True

        if view.action in ("retrieve", "list", "partial_update", "update", "destroy"):
            return obj.user == request.user or request.user.is_superuser

        return True
