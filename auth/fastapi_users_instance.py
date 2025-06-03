from fastapi_users import FastAPIUsers
from uuid import UUID
from models.user import User
from .auth import auth_backend
from .user_manager import get_user_manager

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)