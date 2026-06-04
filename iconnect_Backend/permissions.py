from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Seuls les admins ont accès."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role == 'admin')


class IsTeacher(BasePermission):
    """Seuls les formateurs ont accès."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role in ('teacher', 'admin'))


class IsStudent(BasePermission):
    """Seuls les étudiants ont accès."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role == 'student')


class IsAdminOrTeacher(BasePermission):
    """Admin ou formateur."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role in ('admin', 'teacher'))


class IsOwnerOrAdmin(BasePermission):
    """Propriétaire de l'objet ou admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj == request.user or getattr(obj, 'user', None) == request.user


class IsTeacherOwnerOrAdmin(BasePermission):
    """Formateur propriétaire du cours ou admin."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == 'admin':
            return True
        return getattr(obj, 'teacher', None) == request.user