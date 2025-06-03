from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from models import Product, Client, Status, ProductHistory
from config.statuses import BaseStatus
from typing import Optional, Dict, Any

class ProductHistoryManager:
    """Менеджер для работы с историей действий над товарами."""
    
    # Соответствие статусов и дат
    STATUS_DATES = {
        BaseStatus.CHINA: {
            "date_china": lambda: datetime.now(timezone(timedelta(hours=6))).date(),
            "date_transit": None,
            "date_bishkek": None,
            "take_time": None
        },
        BaseStatus.TRANSIT: {
            "date_china": None,
            "date_transit": lambda: datetime.now(timezone(timedelta(hours=6))).date(),
            "date_bishkek": None,
            "take_time": None
        },
        BaseStatus.BISHKEK: {
            "date_china": None,
            "date_transit": None,  # Не перезаписываем date_transit
            "date_bishkek": lambda: datetime.now(timezone(timedelta(hours=6))).date(),
            "take_time": None
        },
        BaseStatus.PIKED: {
            "date_china": None,
            "date_transit": None,
            "date_bishkek": None,
            "take_time": lambda: datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None)
        }
    }

    @staticmethod
    async def get_status_name(db: AsyncSession, status_id: int) -> str:
        """Получить имя статуса по его ID."""
        query = select(Status).filter(Status.id == status_id)
        result = await db.execute(query)
        status = result.scalars().first()
        return status.name if status else "unknown"

    @staticmethod
    def apply_status_dates(product: Product, status_name: str) -> None:
        """Установить даты в зависимости от статуса, сохраняя существующие."""
        dates = ProductHistoryManager.STATUS_DATES.get(status_name, {})
        # Безопасно обрабатываем каждое поле
        date_china_func = dates.get("date_china", lambda: None)
        product.date_china = product.date_china or (date_china_func() if callable(date_china_func) else None)
        
        date_transit_func = dates.get("date_transit")
        product.date_transit = product.date_transit if date_transit_func is None else (date_transit_func() if callable(date_transit_func) else None)
        
        date_bishkek_func = dates.get("date_bishkek")
        product.date_bishkek = product.date_bishkek if date_bishkek_func is None else (date_bishkek_func() if callable(date_bishkek_func) else None)
        
        take_time_func = dates.get("take_time")
        product.take_time = product.take_time if take_time_func is None else (take_time_func() if callable(take_time_func) else None)

    @staticmethod
    def format_changes(old_data: Dict[str, Any], new_data: Dict[str, Any], client_code: Optional[str] = None) -> str:
        """Форматировать строку изменений для истории."""
        changes = []
        for key, value in new_data.items():
            old_value = old_data.get(key)
            if old_value != value:
                changes.append(f"{key}: {old_value} -> {value}")
        if client_code and old_data.get("client_id") != new_data.get("client_id"):
            changes.append(f"client_code: {old_data.get('client_id')} -> {client_code}")
        return ", ".join(changes) if changes else "без изменений"

    @staticmethod
    async def log_action(
        db: AsyncSession,
        product: Product,
        action: str,
        user: dict,
        client_code: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Создать запись в ProductHistory."""
        status_name = await ProductHistoryManager.get_status_name(db, product.status_id)
        description_parts = [f"Товар {product.product_code} {action} пользователем {user.email}"]
        
        if client_code:
            description_parts.append(f"для клиента {client_code}")
        if action in ["created", "updated"]:
            description_parts.append(f"со статусом {status_name}")
        if old_data and new_data:
            changes = ProductHistoryManager.format_changes(old_data, new_data, client_code)
            description_parts.append(changes)
        
        description = " ".join(description_parts)
        
        history = ProductHistory(
            product_id=product.id,
            action=action,
            action_by_id=user.id,
            action_at=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None),
            description=description
        )
        db.add(history)