from fastapi import HTTPException, status

async def check_superuser_permissions(current_user):
    """
    Проверяет, является ли текущий пользователь суперпользователем.
    
    Args:
        current_user: Объект пользователя, выполняющего действие.
        
    Raises:
        HTTPException: Если пользователь не является суперпользователем.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения действия.",
        )