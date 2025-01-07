from rest_framework import permissions


class IsOwnerOrSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if (
            request.method in permissions.SAFE_METHODS
            and "register-challenge" not in request.build_absolute_uri()
            and "register-coordinator" not in request.build_absolute_uri()
        ):
            return True

        if view.action in ("retrieve", "list", "partial_update", "update", "destroy"):
            if isinstance(obj, dict):
                user = obj["user_attendance"].userprofile.user
            elif hasattr(obj, "userprofile"):
                user = obj.userprofile.user
            else:
                user = obj.user
            return user == request.user or request.user.is_superuser

        return True
