# routers/__init__.py
from fastapi import APIRouter

from .user.router import router as user_router
from .branch.router import router as branch_router
from .client.router import router as client_router
from .status.router import router as status_router
from .product.router import router as product_router
from .payment_method.router import router as payment_method_router
from .payment.router import router as payment_router
from .take.router import router as take
from .report.router import router as report
from .setting.router import router as setting
from .china_address.router import router as china_address
from .default.router import router as default
from .telegram.router import router as telegram
from .text.router import router as text

routers = APIRouter()

routers.include_router(default)
routers.include_router(user_router)
routers.include_router(branch_router)
routers.include_router(client_router)
routers.include_router(status_router)
routers.include_router(product_router)
routers.include_router(payment_method_router)
routers.include_router(payment_router)
routers.include_router(take)
routers.include_router(report)
routers.include_router(setting)
routers.include_router(china_address)
routers.include_router(telegram)
routers.include_router(text)