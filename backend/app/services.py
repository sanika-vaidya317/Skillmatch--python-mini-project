import bcrypt


async def authenticate_user(database, username: str, password: str) -> dict | None:
    user = await database.users.find_one({"username": username.strip().lower()}, {"_id": 0})
    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return user


async def register_user(
    database,
    username: str,
    password: str,
    name: str,
    role: str,
    department: str,
    skills: list[str],
) -> dict | None:
    normalized_username = username.strip().lower()
    if await database.users.find_one({"username": normalized_username}):
        return None
    user = {
        "username": normalized_username,
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "name": name.strip(),
        "role": role,
        "department": department.strip(),
        "skills": skills,
    }
    await database.users.insert_one(user)
    return user