"""
Marketing and Social Domain Models for E-commerce Schema.

This module contains marketing and social-related tables including:
- Marketing campaigns and promotions
- Coupons and discount rules
- Seckill and group buying
- Product reviews and social features
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
# Marketing Domain
# ============================================================================


class MarketingCampaign(Base, TimestampMixin, SoftDeleteMixin):
    """营销活动表"""

    __tablename__ = "mkt_campaign"
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_start_time", "start_time"),
        Index("idx_end_time", "end_time"),
        {"comment": "营销活动表"},
    )

    campaign_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="活动ID")
    campaign_name: Mapped[str] = mapped_column(String(200), comment="活动名称")
    campaign_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="活动类型：1满减/2满折/3秒杀/4拼团/5优惠券/6其他"
    )

    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    apply_scope: Mapped[int] = mapped_column(
        SmallInteger,
        comment="适用范围：1全平台/2指定类目/3指定商品/4指定用户"
    )
    target_rule: Mapped[str | None] = mapped_column(Text, comment="目标规则JSON")

    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="预算金额")
    used_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="已用金额")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0未开始/1进行中/2已结束/3已暂停/4已取消"
    )
    creator_id: Mapped[int] = mapped_column(BigInteger, comment="创建人ID")
    description: Mapped[str | None] = mapped_column(Text, comment="活动描述")


class CouponBatch(Base, TimestampMixin):
    """优惠券批次表"""

    __tablename__ = "mkt_coupon_batch"
    __table_args__ = (
        Index("idx_batch_no", "batch_no"),
        Index("idx_status", "status"),
        {"comment": "优惠券批次表"},
    )

    batch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="批次ID")
    batch_no: Mapped[str] = mapped_column(String(32), unique=True, comment="批次编号")
    batch_name: Mapped[str] = mapped_column(String(200), comment="批次名称")

    coupon_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="优惠券类型：1满减券/2折扣券/3免邮券"
    )
    discount_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="优惠方式：1固定金额/2折扣百分比"
    )
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="优惠额度")

    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="最低订单金额")
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="最高优惠金额")

    total_quantity: Mapped[int] = mapped_column(Integer, comment="发行总量")
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已领取数量")
    used_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已使用数量")

    receive_start_time: Mapped[datetime] = mapped_column(comment="领取开始时间")
    receive_end_time: Mapped[datetime] = mapped_column(comment="领取结束时间")
    valid_days: Mapped[int] = mapped_column(Integer, comment="有效天数")

    receive_limit: Mapped[int] = mapped_column(Integer, default=1, comment="每人限领数量")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class Coupon(Base, TimestampMixin):
    """优惠券表"""

    __tablename__ = "mkt_coupon"
    __table_args__ = (
        Index("idx_batch_id", "batch_id"),
        Index("idx_coupon_code", "coupon_code"),
        Index("idx_status", "status"),
        {"comment": "优惠券表"},
    )

    coupon_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="优惠券ID")
    batch_id: Mapped[int] = mapped_column(BigInteger, comment="批次ID")
    coupon_code: Mapped[str] = mapped_column(String(32), unique=True, comment="优惠券码")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0未发放/1已发放/2已使用/3已过期/4已作废"
    )


class UserCoupon(Base, TimestampMixin):
    """用户优惠券表"""

    __tablename__ = "mkt_user_coupon"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_coupon_id", "coupon_id"),
        Index("idx_status", "status"),
        Index("idx_expire_time", "expire_time"),
        {"comment": "用户优惠券表"},
    )

    user_coupon_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户优惠券ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    coupon_id: Mapped[int] = mapped_column(BigInteger, comment="优惠券ID")
    batch_id: Mapped[int] = mapped_column(BigInteger, comment="批次ID")

    receive_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="领取时间")
    expire_time: Mapped[datetime] = mapped_column(comment="过期时间")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0未使用/1已使用/2已过期"
    )
    use_time: Mapped[datetime | None] = mapped_column(comment="使用时间")
    order_id: Mapped[int | None] = mapped_column(BigInteger, comment="使用订单ID")


class Promotion(Base, TimestampMixin, SoftDeleteMixin):
    """促销活动表"""

    __tablename__ = "mkt_promotion"
    __table_args__ = (
        Index("idx_promotion_type", "promotion_type"),
        Index("idx_status", "status"),
        Index("idx_start_time", "start_time"),
        Index("idx_end_time", "end_time"),
        {"comment": "促销活动表"},
    )

    promotion_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="促销ID")
    promotion_name: Mapped[str] = mapped_column(String(200), comment="促销名称")

    promotion_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="促销类型：1满减/2满折/3满赠/4第N件折扣"
    )

    rule_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="规则类型：1阶梯/2固定"
    )
    rule_config: Mapped[str] = mapped_column(Text, comment="规则配置JSON")

    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级，数值越大越优先")
    can_superpose: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否可叠加：0否/1是")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class Seckill(Base, TimestampMixin):
    """秒杀活动表"""

    __tablename__ = "mkt_seckill"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_status", "status"),
        Index("idx_start_time", "start_time"),
        {"comment": "秒杀活动表"},
    )

    seckill_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="秒杀ID")
    activity_name: Mapped[str] = mapped_column(String(200), comment="活动名称")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    original_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="原价")
    seckill_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="秒杀价")

    total_stock: Mapped[int] = mapped_column(Integer, comment="总库存")
    remaining_stock: Mapped[int] = mapped_column(Integer, comment="剩余库存")
    limit_per_user: Mapped[int] = mapped_column(Integer, default=1, comment="每人限购数量")

    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0未开始/1进行中/2已结束/3已售罄"
    )


class GroupBuy(Base, TimestampMixin):
    """拼团活动表"""

    __tablename__ = "mkt_group_buy"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_status", "status"),
        {"comment": "拼团活动表"},
    )

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="拼团ID")
    activity_name: Mapped[str] = mapped_column(String(200), comment="活动名称")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    original_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="原价")
    group_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="拼团价")

    required_people: Mapped[int] = mapped_column(Integer, comment="成团人数")
    valid_hours: Mapped[int] = mapped_column(Integer, comment="有效时长(小时)")

    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class DiscountRule(Base, TimestampMixin):
    """折扣规则表"""

    __tablename__ = "mkt_discount_rule"
    __table_args__ = (
        Index("idx_rule_type", "rule_type"),
        Index("idx_status", "status"),
        {"comment": "折扣规则表"},
    )

    rule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="规则ID")
    rule_name: Mapped[str] = mapped_column(String(200), comment="规则名称")

    rule_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="规则类型：1会员折扣/2批发折扣/3时段折扣"
    )
    target_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="目标类型：1全平台/2类目/3商品/4用户等级"
    )
    target_ids: Mapped[str | None] = mapped_column(Text, comment="目标ID列表JSON")

    discount_config: Mapped[str] = mapped_column(Text, comment="折扣配置JSON")

    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


# ============================================================================
# Social Domain
# ============================================================================


class ProductComment(Base, TimestampMixin, SoftDeleteMixin):
    """商品评价表"""

    __tablename__ = "soc_comment"
    __table_args__ = (
        Index("idx_product_id", "product_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_order_id", "order_id"),
        Index("idx_rating", "rating"),
        Index("idx_created_at", "created_at"),
        {"comment": "商品评价表"},
    )

    comment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="评价ID")
    order_id: Mapped[int] = mapped_column(BigInteger, comment="订单ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    rating: Mapped[int] = mapped_column(SmallInteger, comment="评分：1-5星")
    content: Mapped[str] = mapped_column(Text, comment="评价内容")
    images: Mapped[str | None] = mapped_column(Text, comment="评价图片JSON")

    is_anonymous: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否匿名：0否/1是")
    is_additional: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否追评：0否/1是")
    additional_comment_id: Mapped[int | None] = mapped_column(BigInteger, comment="原评价ID(追评时)")

    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    reply_count: Mapped[int] = mapped_column(Integer, default=0, comment="回复数")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待审核/1已通过/2已拒绝/3已隐藏"
    )
    audit_time: Mapped[datetime | None] = mapped_column(comment="审核时间")


class CommentReply(Base, TimestampMixin, SoftDeleteMixin):
    """评价回复表"""

    __tablename__ = "soc_reply"
    __table_args__ = (
        Index("idx_comment_id", "comment_id"),
        Index("idx_reply_type", "reply_type"),
        {"comment": "评价回复表"},
    )

    reply_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="回复ID")
    comment_id: Mapped[int] = mapped_column(BigInteger, comment="评价ID")

    reply_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="回复类型：1商家回复/2用户追问/3其他用户"
    )
    replier_id: Mapped[int] = mapped_column(BigInteger, comment="回复人ID")
    replier_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="回复人类型：1用户/2商家/3客服"
    )

    content: Mapped[str] = mapped_column(Text, comment="回复内容")
    reply_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="回复时间")


class UserFollow(Base, TimestampMixin):
    """用户关注表"""

    __tablename__ = "soc_follow"
    __table_args__ = (
        Index("idx_follower_id", "follower_id"),
        Index("idx_followee_id", "followee_id"),
        Index("idx_follow_type", "follow_type"),
        {"comment": "用户关注表"},
    )

    follow_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="关注ID")
    follower_id: Mapped[int] = mapped_column(BigInteger, comment="粉丝ID")
    followee_id: Mapped[int] = mapped_column(BigInteger, comment="被关注者ID")

    follow_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="关注类型：1用户/2商家/3话题"
    )
    follow_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="关注时间")


class UserMessage(Base, TimestampMixin):
    """用户站内信表"""

    __tablename__ = "soc_message"
    __table_args__ = (
        Index("idx_receiver_id", "receiver_id"),
        Index("idx_sender_id", "sender_id"),
        Index("idx_message_type", "message_type"),
        Index("idx_is_read", "is_read"),
        {"comment": "用户站内信表"},
    )

    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="消息ID")
    sender_id: Mapped[int] = mapped_column(BigInteger, comment="发送者ID")
    receiver_id: Mapped[int] = mapped_column(BigInteger, comment="接收者ID")

    message_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="消息类型：1系统通知/2订单消息/3活动通知/4私信"
    )
    title: Mapped[str] = mapped_column(String(200), comment="消息标题")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")

    is_read: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否已读：0否/1是")
    read_time: Mapped[datetime | None] = mapped_column(comment="阅读时间")

    send_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="发送时间")
