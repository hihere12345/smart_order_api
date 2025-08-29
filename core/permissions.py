from rest_framework.permissions import BasePermission

class IsInManagerGroup(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='managers').exists()