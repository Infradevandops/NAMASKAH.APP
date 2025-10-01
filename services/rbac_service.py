from models.rbac_models import Role, Permission, RolePermission, UserRole
from core.database import SessionLocal

class RBACService:
    def __init__(self):
        self.db = SessionLocal()

    def create_role(self, name: str, description: str = None):
        role = Role(name=name, description=description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def create_permission(self, name: str, description: str = None):
        permission = Permission(name=name, description=description)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def assign_permission_to_role(self, role_id: int, permission_id: int):
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        self.db.add(role_permission)
        self.db.commit()
        self.db.refresh(role_permission)
        return role_permission

    def assign_role_to_user(self, user_id: int, role_id: int):
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role

    def get_user_permissions(self, user_id: int):
        permissions = self.db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(UserRole.user_id == user_id).all()
        return permissions

    def has_permission(self, user_id: int, permission_name: str):
        permission = self.db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(UserRole.user_id == user_id, Permission.name == permission_name).first()
        return permission is not None
