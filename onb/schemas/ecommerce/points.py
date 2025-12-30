"""
Points Mall and Gift Card Domain Models for E-commerce Schema.

This module contains points mall and gift card-related tables including:
- Gift cards and batches
- Points mall products
- Points exchange orders
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, TimestampMixin, SoftDeleteMixin


# ============================================================================
# Gift Card Domain
# ============================================================================


class GiftCardBatch(Base, TimestampMixin):
    """礼品卡批次表"""

    __tablename__ = "pts_gift_card_batch"
    __table_args__ = (
        Index("idx_batch_no", "batch_no"),
        Index("idx_status", "status"),
        {"comment": "礼品卡批次表"},
    )

    batch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="批次ID")
    batch_no: Mapped[str] = mapped_column(String(32), unique=True, comment="批次编号")
    batch_name: Mapped[str] = mapped_column(String(200), comment="批次名称")

    card_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="卡类型：1固定面额/2自定义金额"
    )
    face_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="面额(固定面额类型)")
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="最小金额(自定义类型)")
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="最大金额(自定义类型)")

    total_quantity: Mapped[int] = mapped_column(Integer, comment="发行总量")
    issued_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已发放数量")
    activated_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已激活数量")
    used_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已使用数量")

    valid_days: Mapped[int] = mapped_column(Integer, comment="有效天数")
    use_scope: Mapped[int] = mapped_column(
        SmallInteger,
        comment="使用范围：1全平台/2指定类目/3指定商品"
    )
    scope_config: Mapped[str | None] = mapped_column(Text, comment="范围配置JSON")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")
    creator_id: Mapped[int] = mapped_column(BigInteger, comment="创建人ID")


class GiftCard(Base, TimestampMixin):
    """礼品卡表"""

    __tablename__ = "pts_gift_card"
    __table_args__ = (
        Index("idx_batch_id", "batch_id"),
        Index("idx_card_no", "card_no"),
        Index("idx_owner_user_id", "owner_user_id"),
        Index("idx_status", "status"),
        {"comment": "礼品卡表"},
    )

    card_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="卡ID")
    batch_id: Mapped[int] = mapped_column(BigInteger, comment="批次ID")
    card_no: Mapped[str] = mapped_column(String(32), unique=True, comment="卡号")
    card_password: Mapped[str] = mapped_column(String(32), comment="卡密")

    initial_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="初始金额")
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="余额")

    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, comment="持有人用户ID")
    bind_mobile: Mapped[str | None] = mapped_column(String(20), comment="绑定手机号")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0未发放/1已发放/2已激活/3已用完/4已过期/5已作废"
    )

    issue_time: Mapped[datetime | None] = mapped_column(comment="发放时间")
    activate_time: Mapped[datetime | None] = mapped_column(comment="激活时间")
    expire_time: Mapped[datetime] = mapped_column(comment="过期时间")


# ============================================================================
# Points Mall Domain
# ============================================================================


class PointsMallProduct(Base, TimestampMixin, SoftDeleteMixin):
    """积分商城商品表"""

    __tablename__ = "pts_mall_product"
    __table_args__ = (
        Index("idx_product_code", "product_code"),
        Index("idx_status", "status"),
        {"comment": "积分商城商品表"},
    )

    mall_product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="商城商品ID")
    product_code: Mapped[str] = mapped_column(String(32), unique=True, comment="商品编码")
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")

    product_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="商品类型：1实物/2虚拟商品/3优惠券/4礼品卡"
    )
    related_id: Mapped[int | None] = mapped_column(BigInteger, comment="关联ID(SKU/优惠券/礼品卡)")

    main_image: Mapped[str] = mapped_column(String(255), comment="主图")
    images: Mapped[str | None] = mapped_column(Text, comment="图片列表JSON")
    description: Mapped[str | None] = mapped_column(Text, comment="商品描述")

    points_price: Mapped[int] = mapped_column(Integer, comment="积分价格")
    cash_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="现金价格(积分+现金)")

    total_stock: Mapped[int] = mapped_column(Integer, comment="总库存")
    available_stock: Mapped[int] = mapped_column(Integer, comment="可用库存")
    exchange_count: Mapped[int] = mapped_column(Integer, default=0, comment="兑换次数")

    exchange_limit: Mapped[int] = mapped_column(Integer, default=0, comment="限兑数量，0不限")
    start_time: Mapped[datetime | None] = mapped_column(comment="上架时间")
    end_time: Mapped[datetime | None] = mapped_column(comment="下架时间")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待上架/1已上架/2已下架/3已售罄"
    )


class PointsExchangeOrder(Base, TimestampMixin):
    """积分兑换订单表"""

    __tablename__ = "pts_exchange_order"
    __table_args__ = (
        Index("idx_order_no", "order_no"),
        Index("idx_user_id", "user_id"),
        Index("idx_status", "status"),
        {"comment": "积分兑换订单表"},
    )

    exchange_order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="兑换订单ID")
    order_no: Mapped[str] = mapped_column(String(32), unique=True, comment="订单号")

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    mall_product_id: Mapped[int] = mapped_column(BigInteger, comment="商城商品ID")

    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    product_image: Mapped[str | None] = mapped_column(String(255), comment="商品图片")

    quantity: Mapped[int] = mapped_column(Integer, comment="兑换数量")
    points_amount: Mapped[int] = mapped_column(Integer, comment="积分金额")
    cash_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="现金金额")

    address_id: Mapped[int | None] = mapped_column(BigInteger, comment="收货地址ID(实物商品)")
    receiver_name: Mapped[str | None] = mapped_column(String(50), comment="收货人")
    receiver_phone: Mapped[str | None] = mapped_column(String(20), comment="收货电话")
    receiver_address: Mapped[str | None] = mapped_column(String(500), comment="收货地址")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待支付/1待发货/2已发货/3已完成/4已取消/5已退款"
    )

    exchange_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="兑换时间")
    pay_time: Mapped[datetime | None] = mapped_column(comment="支付时间")
    ship_time: Mapped[datetime | None] = mapped_column(comment="发货时间")
    complete_time: Mapped[datetime | None] = mapped_column(comment="完成时间")


class PointsExchangeItem(Base):
    """积分兑换订单明细表"""

    __tablename__ = "pts_exchange_item"
    __table_args__ = (
        Index("idx_exchange_order_id", "exchange_order_id"),
        {"comment": "积分兑换订单明细表"},
    )

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="明细ID")
    exchange_order_id: Mapped[int] = mapped_column(BigInteger, comment="兑换订单ID")

    mall_product_id: Mapped[int] = mapped_column(BigInteger, comment="商城商品ID")
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    product_image: Mapped[str | None] = mapped_column(String(255), comment="商品图片")

    quantity: Mapped[int] = mapped_column(Integer, comment="数量")
    points_price: Mapped[int] = mapped_column(Integer, comment="单价(积分)")
    cash_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="单价(现金)")

    total_points: Mapped[int] = mapped_column(Integer, comment="小计(积分)")
    total_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="小计(现金)")

    delivery_status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="发货状态：0待发货/1已发货/2已签收/3已退货"
    )
    tracking_no: Mapped[str | None] = mapped_column(String(50), comment="物流单号")


class PointsExchangeLog(Base):
    """积分兑换日志表"""

    __tablename__ = "pts_exchange_log"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_exchange_order_id", "exchange_order_id"),
        Index("idx_log_time", "log_time"),
        {"comment": "积分兑换日志表"},
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")
    exchange_order_id: Mapped[int] = mapped_column(BigInteger, comment="兑换订单ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    action_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="操作类型：1创建订单/2支付/3发货/4完成/5取消/6退款"
    )
    points_change: Mapped[int] = mapped_column(Integer, default=0, comment="积分变动")
    cash_change: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="现金变动")

    before_status: Mapped[int] = mapped_column(SmallInteger, comment="操作前状态")
    after_status: Mapped[int] = mapped_column(SmallInteger, comment="操作后状态")

    operator_id: Mapped[int | None] = mapped_column(BigInteger, comment="操作人ID")
    operator_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="操作人类型：1用户/2系统/3管理员"
    )

    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")
    log_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="记录时间")

