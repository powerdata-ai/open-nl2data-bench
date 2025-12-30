"""
E-commerce business scenario schema definitions.

This package contains schema definitions for a complete e-commerce company:

Phase 1: Core Transaction Domain (40 tables)
- order: Order management (15 tables)
- payment: Payment processing (8 tables)
- logistics: Logistics and shipping (10 tables)
- aftersales: After-sales service (7 tables)

Phase 2: Extended Business Domain (27 tables)
- user: User management
- product: Product catalog
- marketing: Marketing and promotions

Phase 3: Supporting Domain (53 tables)
- supply_chain: Supply chain management
- finance: Financial accounting
- hr: Human resources
- data_platform: Data analytics
"""

# Import all models to register them with Base.metadata
# This ensures all tables are available for DDL generation

# Phase 1: Core Transaction Domain (40 tables total)
from onb.schemas.ecommerce.aftersales import (  # noqa: F401
    AfterSalesKnowledge,
    AfterSalesQuality,
    AfterSalesTicket,
)
from onb.schemas.ecommerce.logistics import (  # noqa: F401
    DeliveryRoute,
    Inventory,
    LogisticsCompany,
    PackageInfo,
    ReturnShipping,
    ShippingItem,
    ShippingOrder,
    ShippingTemplate,
    TrackingInfo,
    Warehouse,
)
from onb.schemas.ecommerce.order import (  # noqa: F401
    AfterSalesDispute,
    AfterSalesEvaluation,
    AfterSalesLog,
    InvoiceRequest,
    OrderCancelLog,
    OrderDelivery,
    OrderEvaluation,
    OrderInvoice,
    OrderItem,
    OrderLog,
    OrderMain,
    OrderPayment,
    OrderPromotion,
    OrderRefund,
    OrderSplit,
)
from onb.schemas.ecommerce.payment import (  # noqa: F401
    AccountBalance,
    BalanceLog,
    PaymentCallback,
    PaymentChannel,
    PaymentFlow,
    PaymentOrder,
    RefundFlow,
    SettlementRecord,
)

__all__ = [
    # Order domain (15 tables)
    "OrderMain",
    "OrderItem",
    "OrderPayment",
    "OrderPromotion",
    "OrderLog",
    "OrderEvaluation",
    "OrderCancelLog",
    "OrderSplit",
    "OrderDelivery",
    "OrderInvoice",
    "InvoiceRequest",
    "OrderRefund",
    "AfterSalesLog",
    "AfterSalesDispute",
    "AfterSalesEvaluation",
    # Payment domain (8 tables)
    "PaymentOrder",
    "PaymentChannel",
    "PaymentFlow",
    "RefundFlow",
    "AccountBalance",
    "BalanceLog",
    "PaymentCallback",
    "SettlementRecord",
    # Logistics domain (10 tables)
    "Warehouse",
    "Inventory",
    "LogisticsCompany",
    "ShippingTemplate",
    "ShippingOrder",
    "ShippingItem",
    "TrackingInfo",
    "DeliveryRoute",
    "ReturnShipping",
    "PackageInfo",
    # After-sales service domain (3 additional tables, 7 total with order.py)
    "AfterSalesTicket",
    "AfterSalesKnowledge",
    "AfterSalesQuality",
]
