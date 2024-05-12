import enum


class Role(enum.Enum):
    USER = enum.auto()
    ADMIN = enum.auto()


class Permission(enum.Enum):

    QUERY_SESSION = enum.auto()
    QUERY_USER = enum.auto()
    MODIFY_USER = enum.auto()
    QUERY_ORDER = enum.auto()
    QUERY_SELF_ORDER = enum.auto()
    MODIFY_ORDER = enum.auto()
    QUERY_DESIRE = enum.auto()
    MODIFY_DESIRE = enum.auto()
    QUERY_SELF = enum.auto()


permissions_table = {
    Permission.QUERY_USER: (Role.ADMIN,),
    Permission.QUERY_SELF_ORDER: (Role.USER,Role.ADMIN,),
    Permission.MODIFY_USER: (Role.ADMIN,),
    Permission.QUERY_SESSION: (Role.ADMIN,),
    Permission.QUERY_ORDER: (Role.ADMIN,),
    Permission.MODIFY_ORDER: (Role.ADMIN,),
    Permission.QUERY_DESIRE: (Role.USER,Role.ADMIN,),
    Permission.MODIFY_DESIRE: (Role.USER,Role.ADMIN,),
    Permission.QUERY_SELF: (Role.USER,Role.ADMIN,),
}


def has_permission(role: Role, perm: Permission):
    return role in permissions_table.get(perm, [])


def parse_role(name: str) -> Role:
    for r in Role:
        if name.lower() == r.name.lower():
            return r
    print(f"unknown role from db {name}")
    return Role.USER


def get_permissions(role: Role) -> list[Permission]:
    perms = []
    for perm, roles in permissions_table.items():
        if role in roles:
            perms.append(perm)
    return perms
