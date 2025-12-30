"""
Order domain schema definitions for e-commerce system.

This module contains all order-related tables:
- Order management (main, items, payments)
- Order lifecycle (logs, splits, cancellations)
- Order fulfillment (delivery, invoices)
- After-sales service (refunds, disputes, evaluations)

Total: 15 tables
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, SoftDeleteMixin, TimestampMixin


class OrderMain(Base, TimestampMixin, SoftDeleteMixin):
    """
    订单主表 - 存储订单基本信息和状态.

    业务说明：
    - 每个订单对应一次下单行为
    - 支持订单拆分（拆分后生成多个子订单）
    - 订单状态流转：待支付 → 已支付 → 已发货 → 已完成/已取消
    """

    __tablename__ = "ord_order_main"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_order_time", "order_time"),
        Index("idx_order_status", "order_status"),
        Index("idx_parent_order", "parent_order_id"),
        {"comment": "订单主表"},
    )

    # 主键
    order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="订单ID")

    # 业务主键
    order_no: Mapped[str] = mapped_column(String(32), unique=True, comment="订单号")

    # 关联信息
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    parent_order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="父订单ID（订单拆分时使用）"
    )

    # 金额信息
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="订单总金额（商品金额之和）"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="优惠金额（促销+优惠券）"
    )
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="运费"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="实付金额（总金额-优惠+运费）"
    )

    # 状态信息
    order_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="订单状态：0待支付/1已支付/2待发货/3已发货/4已完成/5已取消/6已关闭",
    )
    payment_status: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="支付状态：0未支付/1部分支付/2已支付/3已退款"
    )
    shipping_status: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="发货状态：0未发货/1部分发货/2已发货/3已签收"
    )
    refund_status: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="退款状态：0无退款/1退款中/2部分退款/3全部退款"
    )

    # 营销信息
    promotion_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="促销活动ID"
    )
    coupon_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="优惠券ID"
    )

    # 地址信息
    shipping_address_id: Mapped[int] = mapped_column(BigInteger, comment="收货地址ID")

    # 时间信息
    order_time: Mapped[datetime] = mapped_column(DateTime, comment="下单时间")
    payment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="支付时间"
    )
    shipping_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="发货时间"
    )
    complete_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )
    cancel_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="取消时间"
    )

    # 其他信息
    order_source: Mapped[int] = mapped_column(
        SmallInteger, comment="订单来源：1PC/2H5/3小程序/4APP/5API"
    )
    buyer_message: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="买家留言"
    )


class OrderItem(Base, TimestampMixin):
    """
    订单明细表 - 存储订单中的商品明细信息.

    业务说明：
    - 一个订单可以包含多个商品（多条明细）
    - 保存下单时的商品快照信息（价格、属性等）
    - 支持单品退款
    """

    __tablename__ = "ord_order_item"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_product_id", "product_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "订单明细表"},
    )

    # 主键
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="明细ID")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    # 商品信息快照（下单时的状态）
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    sku_name: Mapped[str] = mapped_column(String(200), comment="SKU名称")
    sku_attrs: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="SKU属性JSON（颜色、尺码等）"
    )
    product_image: Mapped[str] = mapped_column(String(500), comment="商品图片URL")

    # 价格数量
    original_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="商品原价（单价）"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="成交单价（可能含促销）"
    )
    quantity: Mapped[int] = mapped_column(SmallInteger, comment="购买数量")
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="优惠金额"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="实付金额（单价*数量-优惠）"
    )

    # 退款信息
    refund_quantity: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="已退款数量"
    )
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="已退款金额"
    )

    # 状态
    item_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="明细状态：1正常/2已退款/3已取消"
    )


class OrderPayment(Base, TimestampMixin):
    """
    订单支付表 - 记录订单的支付流水.

    业务说明：
    - 一个订单可能有多条支付记录（部分支付、补差价等）
    - 记录支付方式、支付金额、第三方支付流水号等
    """

    __tablename__ = "ord_order_payment"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_payment_no", "payment_no"),
        Index("idx_trade_no", "trade_no"),
        {"comment": "订单支付表"},
    )

    # 主键
    payment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="支付ID")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )

    # 支付信息
    payment_no: Mapped[str] = mapped_column(String(32), unique=True, comment="支付流水号")
    payment_method: Mapped[int] = mapped_column(
        SmallInteger, comment="支付方式：1支付宝/2微信/3银行卡/4余额/5货到付款"
    )
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="支付金额")

    # 第三方支付信息
    trade_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="第三方支付流水号"
    )
    payment_channel: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="支付渠道（如：支付宝、微信支付）"
    )

    # 状态和时间
    payment_status: Mapped[int] = mapped_column(
        SmallInteger, comment="支付状态：0待支付/1支付中/2已支付/3支付失败/4已退款"
    )
    payment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="支付完成时间"
    )

    # 其他信息
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )


class OrderPromotion(Base, TimestampMixin):
    """
    订单促销表 - 记录订单使用的促销活动.

    业务说明：
    - 一个订单可以使用多种促销（满减、折扣、赠品等）
    - 记录促销类型、优惠金额等
    """

    __tablename__ = "ord_order_promotion"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_promotion_id", "promotion_id"),
        {"comment": "订单促销表"},
    )

    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    promotion_id: Mapped[int] = mapped_column(BigInteger, comment="促销活动ID")

    # 促销信息
    promotion_type: Mapped[int] = mapped_column(
        SmallInteger, comment="促销类型：1满减/2折扣/3满赠/4优惠券/5积分抵扣"
    )
    promotion_name: Mapped[str] = mapped_column(String(100), comment="促销活动名称")
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="优惠金额"
    )

    # 促销规则快照
    rule_desc: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="促销规则描述"
    )


class OrderLog(Base):
    """
    订单日志表 - 记录订单状态变更历史.

    业务说明：
    - 记录订单的所有状态变更操作
    - 用于追溯订单处理流程和异常排查
    """

    __tablename__ = "ord_order_log"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_created_at", "created_at"),
        {"comment": "订单日志表"},
    )

    # 主键
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )

    # 日志内容
    operation_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="操作类型：1创建订单/2支付/3发货/4签收/5评价/6取消/7退款",
    )
    operation_desc: Mapped[str] = mapped_column(String(500), comment="操作描述")
    old_status: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, comment="变更前状态"
    )
    new_status: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, comment="变更后状态"
    )

    # 操作人信息
    operator_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="操作人ID（用户或管理员）"
    )
    operator_type: Mapped[int] = mapped_column(
        SmallInteger, comment="操作人类型：1用户/2系统/3管理员"
    )

    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )


class OrderEvaluation(Base, TimestampMixin):
    """
    订单评价表 - 存储用户对订单的评价.

    业务说明：
    - 用户确认收货后可以对订单进行评价
    - 包含商品评分、服务评分、物流评分等
    """

    __tablename__ = "ord_order_evaluation"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_user_id", "user_id"),
        {"comment": "订单评价表"},
    )

    # 主键
    evaluation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="评价ID"
    )

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 评分（1-5星）
    product_score: Mapped[int] = mapped_column(SmallInteger, comment="商品评分（1-5）")
    service_score: Mapped[int] = mapped_column(SmallInteger, comment="服务评分（1-5）")
    logistics_score: Mapped[int] = mapped_column(SmallInteger, comment="物流评分（1-5）")

    # 评价内容
    evaluation_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="评价内容"
    )
    evaluation_images: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="评价图片（JSON数组）"
    )

    # 状态
    evaluation_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="评价状态：1待审核/2已发布/3已屏蔽"
    )
    is_anonymous: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="是否匿名：0否/1是"
    )

    # 追评
    append_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="追加评价内容"
    )
    append_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="追评时间"
    )


class OrderCancelLog(Base, TimestampMixin):
    """
    订单取消日志表 - 记录订单取消的详细信息.

    业务说明：
    - 记录订单取消的原因、时间、操作人等信息
    - 用于分析订单取消原因和优化流程
    """

    __tablename__ = "ord_order_cancel_log"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_cancel_time", "cancel_time"),
        {"comment": "订单取消日志表"},
    )

    # 主键
    cancel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="取消ID")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )

    # 取消信息
    cancel_reason_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="取消原因类型：1不想要了/2信息填错/3重复下单/4商品缺货/5价格变动/6其他",
    )
    cancel_reason: Mapped[str] = mapped_column(String(500), comment="取消原因详细描述")

    # 操作人信息
    operator_id: Mapped[int] = mapped_column(BigInteger, comment="操作人ID")
    operator_type: Mapped[int] = mapped_column(
        SmallInteger, comment="操作人类型：1用户/2系统/3管理员"
    )

    # 时间
    cancel_time: Mapped[datetime] = mapped_column(DateTime, comment="取消时间")


class OrderSplit(Base, TimestampMixin):
    """
    订单拆分表 - 记录订单拆分信息.

    业务说明：
    - 当订单包含多个商家的商品时，需要拆分成多个子订单
    - 记录拆分原因和拆分后的订单关系
    """

    __tablename__ = "ord_order_split"
    __table_args__ = (
        Index("idx_parent_order", "parent_order_id"),
        Index("idx_child_order", "child_order_id"),
        {"comment": "订单拆分表"},
    )

    # 主键
    split_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="拆分ID")

    # 订单关系
    parent_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="父订单ID"
    )
    child_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="子订单ID"
    )

    # 拆分信息
    split_reason: Mapped[int] = mapped_column(
        SmallInteger, comment="拆分原因：1多商家/2部分发货/3库存不足/4其他"
    )
    split_desc: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="拆分说明"
    )


class OrderDelivery(Base, TimestampMixin):
    """
    订单配送表 - 记录订单的物流配送信息.

    业务说明：
    - 一个订单可能有多次配送（部分发货）
    - 记录物流公司、运单号、配送状态等
    """

    __tablename__ = "ord_order_delivery"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_tracking_no", "tracking_no"),
        {"comment": "订单配送表"},
    )

    # 主键
    delivery_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="配送ID"
    )

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )

    # 物流信息
    logistics_company: Mapped[str] = mapped_column(String(100), comment="物流公司")
    tracking_no: Mapped[str] = mapped_column(String(50), comment="物流单号")

    # 配送状态
    delivery_status: Mapped[int] = mapped_column(
        SmallInteger, comment="配送状态：1待揽收/2运输中/3派送中/4已签收/5异常"
    )

    # 时间信息
    ship_time: Mapped[datetime] = mapped_column(DateTime, comment="发货时间")
    receive_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="签收时间"
    )

    # 收货人信息快照
    receiver_name: Mapped[str] = mapped_column(String(50), comment="收货人姓名")
    receiver_phone: Mapped[str] = mapped_column(String(20), comment="收货人电话")
    receiver_address: Mapped[str] = mapped_column(String(500), comment="收货地址")


class InvoiceRequest(Base, TimestampMixin):
    """
    发票申请表 - 存储用户的发票申请信息.

    业务说明：
    - 用户下单时或完成后可以申请发票
    - 支持普通发票和增值税专用发票
    """

    __tablename__ = "ord_invoice_request"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_user_id", "user_id"),
        {"comment": "发票申请表"},
    )

    # 主键
    request_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="申请ID"
    )

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 发票类型和抬头
    invoice_type: Mapped[int] = mapped_column(
        SmallInteger, comment="发票类型：1普通发票/2增值税专用发票"
    )
    invoice_title_type: Mapped[int] = mapped_column(
        SmallInteger, comment="抬头类型：1个人/2企业"
    )
    invoice_title: Mapped[str] = mapped_column(String(200), comment="发票抬头")

    # 企业信息（专用发票必填）
    tax_no: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="纳税人识别号"
    )
    company_address: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="公司地址"
    )
    company_phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="公司电话"
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="开户银行"
    )
    bank_account: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="银行账号"
    )

    # 发票金额
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="发票金额")

    # 状态
    request_status: Mapped[int] = mapped_column(
        SmallInteger, comment="申请状态：1待处理/2已开票/3已拒绝"
    )


class OrderInvoice(Base, TimestampMixin):
    """
    订单发票表 - 记录已开具的发票信息.

    业务说明：
    - 发票申请通过后生成发票记录
    - 记录发票号、开票时间等信息
    """

    __tablename__ = "ord_order_invoice"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_request_id", "request_id"),
        Index("idx_invoice_no", "invoice_no"),
        {"comment": "订单发票表"},
    )

    # 主键
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="发票ID"
    )

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_invoice_request.request_id"), comment="申请ID"
    )

    # 发票信息
    invoice_no: Mapped[str] = mapped_column(String(50), unique=True, comment="发票号码")
    invoice_code: Mapped[str] = mapped_column(String(50), comment="发票代码")
    invoice_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="电子发票URL"
    )

    # 开票时间
    issue_time: Mapped[datetime] = mapped_column(DateTime, comment="开票时间")


class OrderRefund(Base, TimestampMixin):
    """
    退款单表 - 记录订单退款信息.

    业务说明：
    - 用户申请退款后生成退款单
    - 支持整单退款和单品退款
    - 退款流程：申请 → 审核 → 退款 → 完成
    """

    __tablename__ = "ord_refund"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_refund_no", "refund_no"),
        Index("idx_user_id", "user_id"),
        {"comment": "退款单表"},
    )

    # 主键
    refund_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="退款ID")

    # 业务主键
    refund_no: Mapped[str] = mapped_column(String(32), unique=True, comment="退款单号")

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    item_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("ord_order_item.item_id"),
        nullable=True,
        comment="订单明细ID（单品退款时使用）",
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 退款信息
    refund_type: Mapped[int] = mapped_column(
        SmallInteger, comment="退款类型：1仅退款/2退货退款"
    )
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="退款金额")
    refund_quantity: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="退款数量（退货时使用）"
    )

    # 退款原因
    refund_reason: Mapped[str] = mapped_column(String(500), comment="退款原因")
    refund_desc: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="退款说明"
    )
    refund_images: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="退款凭证图片（JSON数组）"
    )

    # 状态和流程
    refund_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="退款状态：0待审核/1已同意/2已拒绝/3退货中/4已退款/5已完成/6已取消",
    )

    # 审核信息
    approve_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="审核人ID"
    )
    approve_remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="审核备注"
    )

    # 时间信息
    apply_time: Mapped[datetime] = mapped_column(DateTime, comment="申请时间")
    approve_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="审核时间"
    )
    refund_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="退款时间"
    )
    complete_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )


class AfterSalesLog(Base):
    """
    售后日志表 - 记录售后流程的操作日志.

    业务说明：
    - 记录退款、退货、换货等售后操作的详细流程
    - 用于追溯售后处理过程
    """

    __tablename__ = "ord_aftersales_log"
    __table_args__ = (
        Index("idx_refund_id", "refund_id"),
        Index("idx_created_at", "created_at"),
        {"comment": "售后日志表"},
    )

    # 主键
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")

    # 关联信息
    refund_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_refund.refund_id"), comment="退款单ID"
    )

    # 日志内容
    operation_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="操作类型：1申请退款/2审核通过/3审核拒绝/4退货/5退款/6完成/7取消",
    )
    operation_desc: Mapped[str] = mapped_column(String(500), comment="操作描述")

    # 操作人信息
    operator_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="操作人ID"
    )
    operator_type: Mapped[int] = mapped_column(
        SmallInteger, comment="操作人类型：1用户/2系统/3客服"
    )

    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )


class AfterSalesDispute(Base, TimestampMixin):
    """
    售后纠纷表 - 记录售后过程中的纠纷信息.

    业务说明：
    - 当退款/退货申请被拒绝时，用户可以发起纠纷
    - 平台客服介入处理
    """

    __tablename__ = "ord_aftersales_dispute"
    __table_args__ = (
        Index("idx_refund_id", "refund_id"),
        Index("idx_dispute_status", "dispute_status"),
        {"comment": "售后纠纷表"},
    )

    # 主键
    dispute_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="纠纷ID"
    )

    # 关联信息
    refund_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_refund.refund_id"), comment="退款单ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 纠纷信息
    dispute_reason: Mapped[str] = mapped_column(String(500), comment="纠纷原因")
    dispute_desc: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="纠纷详细说明"
    )
    dispute_images: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="纠纷凭证图片（JSON数组）"
    )

    # 处理信息
    dispute_status: Mapped[int] = mapped_column(
        SmallInteger, comment="纠纷状态：1待处理/2处理中/3已解决/4已关闭"
    )
    handler_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="处理人ID（客服）"
    )
    handle_result: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="处理结果"
    )

    # 时间
    dispute_time: Mapped[datetime] = mapped_column(DateTime, comment="发起时间")
    handle_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="处理时间"
    )


class AfterSalesEvaluation(Base, TimestampMixin):
    """
    售后评价表 - 用户对售后服务的评价.

    业务说明：
    - 售后完成后用户可以评价售后服务质量
    - 用于改进售后服务流程
    """

    __tablename__ = "ord_aftersales_evaluation"
    __table_args__ = (
        Index("idx_refund_id", "refund_id"),
        Index("idx_user_id", "user_id"),
        {"comment": "售后评价表"},
    )

    # 主键
    evaluation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="评价ID"
    )

    # 关联信息
    refund_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_refund.refund_id"), comment="退款单ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 评价内容
    service_score: Mapped[int] = mapped_column(SmallInteger, comment="服务评分（1-5）")
    process_score: Mapped[int] = mapped_column(SmallInteger, comment="流程评分（1-5）")
    speed_score: Mapped[int] = mapped_column(SmallInteger, comment="速度评分（1-5）")

    evaluation_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="评价内容"
    )

    # 状态
    evaluation_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="评价状态：1待审核/2已发布/3已屏蔽"
    )
