"""
E-commerce business scenario schema definitions.

This package contains schema definitions for a complete e-commerce company with 120 tables:

Phase 1: Core Transaction Domain (36 tables)
- order: Order management (15 tables)
  * ord_order_main, ord_order_item, ord_order_payment, ord_order_promotion,
  * ord_order_log, ord_order_evaluation, ord_order_cancel_log, ord_order_split,
  * ord_order_delivery, ord_order_invoice, ord_invoice_request, ord_refund,
  * ord_aftersales_log, ord_aftersales_dispute, ord_aftersales_evaluation
- payment: Payment processing (8 tables)
  * pay_payment_order, pay_payment_channel, pay_payment_flow, pay_refund_flow,
  * pay_account_balance, pay_balance_log, pay_payment_callback, pay_settlement_record
- logistics: Logistics and shipping (10 tables)
  * log_warehouse, log_inventory, log_logistics_company, log_shipping_template,
  * log_shipping_order, log_shipping_item, log_tracking_info, log_delivery_route,
  * log_return_shipping, log_package_info
- aftersales: After-sales service (3 tables)
  * afs_ticket, afs_knowledge, afs_quality

Phase 2: Product & Inventory Domain (23 tables)
- product: Product catalog (10 tables)
  * prd_category, prd_brand, prd_product, prd_sku, prd_attribute,
  * prd_attribute_value, prd_sku_attribute, prd_image, prd_description,
  * prd_price_history
- inventory: Stock management (7 tables)
  * inv_stock, inv_stock_log, inv_allocation, inv_reservation,
  * inv_adjustment, inv_transfer, inv_safety_stock
- supplier: Supplier and purchasing (6 tables)
  * sup_supplier, sup_product, sup_purchase_order, sup_purchase_item,
  * sup_receiving, sup_quality_check

Phase 3: User & Marketing Domain (23 tables)
- user: User management (11 tables)
  * usr_user, usr_profile, usr_address, usr_favorite, usr_browsing_history,
  * usr_search_history, usr_cart, usr_growth, usr_level, usr_points
- marketing: Marketing and promotions (8 tables)
  * mkt_campaign, mkt_coupon_batch, mkt_coupon, mkt_user_coupon,
  * mkt_promotion, mkt_seckill, mkt_group_buy, mkt_discount_rule
- social: Social features (4 tables)
  * soc_comment, soc_reply, soc_follow, soc_message

Phase 4: Data & Operations Domain (20 tables)
- cms: Content management (4 tables)
  * cms_article, cms_banner, cms_topic, cms_navigation
- customer: Customer service (4 tables)
  * cus_ticket, cus_conversation, cus_message, cus_satisfaction
- analytics: Data analysis (4 tables)
  * ana_user_behavior, ana_sales_daily, ana_product_view, ana_conversion
- system: System configuration (5 tables)
  * sys_config, sys_dict, sys_region, sys_express, sys_notification

Phase 5: Search & Recommendation Domain (8 tables)
- search: Search functionality (5 tables)
  * sea_query, sea_result, sea_hot_search, sea_synonym, sea_filter
- recommendation: Product recommendation (3 tables)
  * sea_recommend_strategy, sea_product_recommend, sea_user_recommend

Phase 6: Points Mall & Gift Card Domain (6 tables)
- giftcard: Gift card management (2 tables)
  * pts_gift_card_batch, pts_gift_card
- pointsmall: Points exchange (4 tables)
  * pts_mall_product, pts_exchange_order, pts_exchange_item, pts_exchange_log

Phase 7: Merchant & Store Domain (8 tables)
- merchant: Merchant management (4 tables)
  * mch_merchant, mch_category, mch_account, mch_settlement
- store: Physical store operations (4 tables)
  * mch_store, mch_store_staff, mch_store_inventory, mch_store_order

Total: 120 tables covering complete e-commerce business operations
"""

# Import all models to register them with Base.metadata
# This ensures all tables are available for DDL generation

# Phase 1: Core Transaction Domain (36 tables total)
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

# Phase 2: Product & Inventory Domain (33 tables total)
from onb.schemas.ecommerce.product import (  # noqa: F401
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductBrand,
    ProductCategory,
    ProductDescription,
    ProductImage,
    ProductPriceHistory,
    ProductSKU,
    ProductSKUAttribute,
)
from onb.schemas.ecommerce.inventory import (  # noqa: F401
    InventoryAdjustment,
    InventoryAllocation,
    InventoryReservation,
    InventorySafetyStock,
    InventoryStock,
    InventoryStockLog,
    InventoryTransfer,
    PurchaseItem,
    PurchaseOrder,
    PurchaseReceiving,
    QualityCheck,
    Supplier,
    SupplierProduct,
)

# Phase 3: User & Marketing Domain (26 tables total)
from onb.schemas.ecommerce.user import (  # noqa: F401
    User,
    UserProfile,
    UserAddress,
    UserFavorite,
    UserBrowsingHistory,
    UserSearchHistory,
    UserCart,
    UserGrowth,
    UserLevel,
    UserPoints,
)
from onb.schemas.ecommerce.marketing import (  # noqa: F401
    MarketingCampaign,
    CouponBatch,
    Coupon,
    UserCoupon,
    Promotion,
    Seckill,
    GroupBuy,
    DiscountRule,
    ProductComment,
    CommentReply,
    UserFollow,
    UserMessage,
)

# Phase 4: Data & Operations Domain (20 tables total)
from onb.schemas.ecommerce.operations import (  # noqa: F401
    CMSArticle,
    CMSBanner,
    CMSTopic,
    CMSNavigation,
    CustomerTicket,
    CustomerConversation,
    CustomerMessage,
    CustomerSatisfaction,
    UserBehavior,
    SalesDaily,
    ProductView,
    ConversionFunnel,
    SystemConfig,
    SystemDict,
    SystemRegion,
    ExpressCompany,
    NotificationTemplate,
)

# Phase 5: Search & Recommendation Domain (8 tables total)
from onb.schemas.ecommerce.search import (  # noqa: F401
    SearchQuery,
    SearchResult,
    HotSearch,
    SearchSynonym,
    SearchFilter,
    RecommendStrategy,
    ProductRecommend,
    UserRecommend,
)

# Phase 6: Points Mall & Gift Card Domain (6 tables total)
from onb.schemas.ecommerce.points import (  # noqa: F401
    GiftCardBatch,
    GiftCard,
    PointsMallProduct,
    PointsExchangeOrder,
    PointsExchangeItem,
    PointsExchangeLog,
)

# Phase 7: Merchant & Store Domain (8 tables total)
from onb.schemas.ecommerce.merchant import (  # noqa: F401
    Merchant,
    MerchantCategory,
    MerchantAccount,
    MerchantSettlement,
    Store,
    StoreStaff,
    StoreInventory,
    StoreOrder,
)

__all__ = [
    # Order domain (11 tables)
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
    # After-sales domain (7 tables including those in order.py)
    "OrderRefund",
    "AfterSalesLog",
    "AfterSalesDispute",
    "AfterSalesEvaluation",
    "AfterSalesTicket",
    "AfterSalesKnowledge",
    "AfterSalesQuality",
    # Product domain (10 tables)
    "ProductCategory",
    "ProductBrand",
    "Product",
    "ProductSKU",
    "ProductAttribute",
    "ProductAttributeValue",
    "ProductSKUAttribute",
    "ProductImage",
    "ProductDescription",
    "ProductPriceHistory",
    # Inventory domain (7 tables)
    "InventoryStock",
    "InventoryStockLog",
    "InventoryAllocation",
    "InventoryReservation",
    "InventoryAdjustment",
    "InventoryTransfer",
    "InventorySafetyStock",
    # Supplier domain (6 tables)
    "Supplier",
    "SupplierProduct",
    "PurchaseOrder",
    "PurchaseItem",
    "PurchaseReceiving",
    "QualityCheck",
    # User domain (11 tables)
    "User",
    "UserProfile",
    "UserAddress",
    "UserFavorite",
    "UserBrowsingHistory",
    "UserSearchHistory",
    "UserCart",
    "UserGrowth",
    "UserLevel",
    "UserPoints",
    # Marketing domain (12 tables)
    "MarketingCampaign",
    "CouponBatch",
    "Coupon",
    "UserCoupon",
    "Promotion",
    "Seckill",
    "GroupBuy",
    "DiscountRule",
    "ProductComment",
    "CommentReply",
    "UserFollow",
    "UserMessage",
    # CMS domain (4 tables)
    "CMSArticle",
    "CMSBanner",
    "CMSTopic",
    "CMSNavigation",
    # Customer Service domain (4 tables)
    "CustomerTicket",
    "CustomerConversation",
    "CustomerMessage",
    "CustomerSatisfaction",
    # Analytics domain (4 tables)
    "UserBehavior",
    "SalesDaily",
    "ProductView",
    "ConversionFunnel",
    # System domain (5 tables)
    "SystemConfig",
    "SystemDict",
    "SystemRegion",
    "ExpressCompany",
    "NotificationTemplate",
    # Search & Recommendation domain (8 tables)
    "SearchQuery",
    "SearchResult",
    "HotSearch",
    "SearchSynonym",
    "SearchFilter",
    "RecommendStrategy",
    "ProductRecommend",
    "UserRecommend",
    # Points Mall & Gift Card domain (6 tables)
    "GiftCardBatch",
    "GiftCard",
    "PointsMallProduct",
    "PointsExchangeOrder",
    "PointsExchangeItem",
    "PointsExchangeLog",
    # Merchant & Store domain (8 tables)
    "Merchant",
    "MerchantCategory",
    "MerchantAccount",
    "MerchantSettlement",
    "Store",
    "StoreStaff",
    "StoreInventory",
    "StoreOrder",
]
