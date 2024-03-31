import enum


class Role(enum.Enum):
    USER = ()
    ADMIN = ()


class Permission(enum.Enum):

    QUERY_SESSIONS = ()
    QUERY_USERS = ()


permissions_table = {
    Permission.QUERY_USERS: (Role.ADMIN,),
    Permission.QUERY_SESSIONS: (Role.ADMIN,)
}


def has_permission(role: Role, perm: Permission):
    return role in permissions_table.get(perm, [])


def parse_role(name) -> Role or None:
    for r in Role:
        if name.lower() == r.name.lower():
            return r
    return None


def get_permissions(role: Role) -> list[Permission]:
    perms = []
    for perm, roles in permissions_table.items():
        if role in roles:
            perms.append(perm)
    return perms
