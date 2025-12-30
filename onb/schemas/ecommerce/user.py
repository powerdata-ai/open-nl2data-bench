"""
User and Marketing Domain Models for E-commerce Schema.

This module contains user and marketing-related tables including:
- User management and profiles
- User addresses and favorites
- Shopping cart
- Member system (levels, points, growth)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, TimestampMixin, SoftDeleteMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    """用户基础信息表"""

    __tablename__ = "usr_user"
    __table_args__ = (
        Index("idx_mobile", "mobile"),
        Index("idx_email", "email"),
        Index("idx_status", "status"),
        Index("idx_register_time", "register_time"),
        {"comment": "用户基础信息表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, comment="用户名")
    mobile: Mapped[str | None] = mapped_column(String(20), unique=True, comment="手机号")
    email: Mapped[str | None] = mapped_column(String(100), unique=True, comment="邮箱")

    password_hash: Mapped[str] = mapped_column(String(128), comment="密码哈希")
    salt: Mapped[str] = mapped_column(String(32), comment="密码盐值")

    nickname: Mapped[str | None] = mapped_column(String(50), comment="昵称")
    avatar_url: Mapped[str | None] = mapped_column(String(255), comment="头像URL")
    gender: Mapped[int] = mapped_column(SmallInteger, default=0, comment="性别：0未知/1男/2女")
    birthday: Mapped[datetime | None] = mapped_column(Date, comment="生日")

    register_source: Mapped[int] = mapped_column(
        SmallInteger,
        comment="注册来源：1Web/2iOS/3Android/4WeChat/5其他"
    )
    register_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="注册时间")
    last_login_time: Mapped[datetime | None] = mapped_column(comment="最后登录时间")
    last_login_ip: Mapped[str | None] = mapped_column(String(50), comment="最后登录IP")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=1,
        comment="状态：0禁用/1正常/2冻结"
    )


class UserProfile(Base, TimestampMixin):
    """用户画像表"""

    __tablename__ = "usr_profile"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_level_id", "level_id"),
        {"comment": "用户画像表"},
    )

    profile_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="画像ID")
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, comment="用户ID")

    # Member info
    level_id: Mapped[int] = mapped_column(BigInteger, default=1, comment="会员等级ID")
    growth_value: Mapped[int] = mapped_column(Integer, default=0, comment="成长值")
    points: Mapped[int] = mapped_column(Integer, default=0, comment="积分")

    # Statistics
    total_orders: Mapped[int] = mapped_column(Integer, default=0, comment="总订单数")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="累计消费金额")
    avg_order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="平均订单金额")

    last_order_time: Mapped[datetime | None] = mapped_column(comment="最后下单时间")
    favorite_category: Mapped[str | None] = mapped_column(String(200), comment="偏好类目")

    # RFM model
    rfm_score: Mapped[int | None] = mapped_column(Integer, comment="RFM总分")
    recency_score: Mapped[int | None] = mapped_column(Integer, comment="最近购买得分")
    frequency_score: Mapped[int | None] = mapped_column(Integer, comment="购买频率得分")
    monetary_score: Mapped[int | None] = mapped_column(Integer, comment="购买金额得分")

    # Tags
    user_tags: Mapped[str | None] = mapped_column(String(500), comment="用户标签(JSON)")


class UserAddress(Base, TimestampMixin, SoftDeleteMixin):
    """用户收货地址表"""

    __tablename__ = "usr_address"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_is_default", "is_default"),
        {"comment": "用户收货地址表"},
    )

    address_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="地址ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    receiver_name: Mapped[str] = mapped_column(String(50), comment="收货人姓名")
    receiver_phone: Mapped[str] = mapped_column(String(20), comment="收货人电话")

    province: Mapped[str] = mapped_column(String(50), comment="省份")
    city: Mapped[str] = mapped_column(String(50), comment="城市")
    district: Mapped[str] = mapped_column(String(50), comment="区县")
    detail_address: Mapped[str] = mapped_column(String(500), comment="详细地址")
    postal_code: Mapped[str | None] = mapped_column(String(10), comment="邮编")

    address_label: Mapped[str | None] = mapped_column(String(20), comment="地址标签：家/公司/学校")
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否默认地址：0否/1是")


class UserFavorite(Base, TimestampMixin):
    """用户收藏表"""

    __tablename__ = "usr_favorite"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_product_id", "product_id"),
        Index("idx_favorite_time", "favorite_time"),
        {"comment": "用户收藏表"},
    )

    favorite_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="收藏ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")

    favorite_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="收藏时间")
    is_notified: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否已通知降价：0否/1是")


class UserBrowsingHistory(Base):
    """用户浏览历史表"""

    __tablename__ = "usr_browsing_history"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_product_id", "product_id"),
        Index("idx_browse_time", "browse_time"),
        {"comment": "用户浏览历史表"},
    )

    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="历史ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")

    browse_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="浏览时间")
    browse_duration: Mapped[int | None] = mapped_column(Integer, comment="浏览时长(秒)")
    source_page: Mapped[str | None] = mapped_column(String(100), comment="来源页面")


class UserSearchHistory(Base):
    """用户搜索历史表"""

    __tablename__ = "usr_search_history"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_keyword", "keyword"),
        Index("idx_search_time", "search_time"),
        {"comment": "用户搜索历史表"},
    )

    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="历史ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    keyword: Mapped[str] = mapped_column(String(200), comment="搜索关键词")
    result_count: Mapped[int | None] = mapped_column(Integer, comment="搜索结果数")
    clicked_product_id: Mapped[int | None] = mapped_column(BigInteger, comment="点击的商品ID")

    search_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="搜索时间")


class UserCart(Base, TimestampMixin):
    """购物车表"""

    __tablename__ = "usr_cart"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "购物车表"},
    )

    cart_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="购物车ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    quantity: Mapped[int] = mapped_column(Integer, comment="数量")
    is_checked: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否选中：0否/1是")
    is_valid: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否有效：0否/1是")


class UserGrowth(Base):
    """用户成长值记录表"""

    __tablename__ = "usr_growth"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_change_time", "change_time"),
        {"comment": "用户成长值记录表"},
    )

    growth_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="成长值ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    change_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="变动类型：1增加/2减少"
    )
    change_value: Mapped[int] = mapped_column(Integer, comment="变动值")
    before_value: Mapped[int] = mapped_column(Integer, comment="变动前成长值")
    after_value: Mapped[int] = mapped_column(Integer, comment="变动后成长值")

    source_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="来源类型：1购物/2评价/3签到/4活动/5其他"
    )
    source_id: Mapped[str | None] = mapped_column(String(64), comment="来源ID")

    remark: Mapped[str | None] = mapped_column(String(200), comment="备注")
    change_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="变动时间")


class UserLevel(Base, TimestampMixin):
    """会员等级配置表"""

    __tablename__ = "usr_level"
    __table_args__ = (
        Index("idx_level", "level"),
        {"comment": "会员等级配置表"},
    )

    level_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="等级ID")
    level: Mapped[int] = mapped_column(Integer, unique=True, comment="等级：1/2/3...")
    level_name: Mapped[str] = mapped_column(String(50), comment="等级名称")
    level_icon: Mapped[str | None] = mapped_column(String(255), comment="等级图标")

    min_growth: Mapped[int] = mapped_column(Integer, comment="最小成长值")
    max_growth: Mapped[int | None] = mapped_column(Integer, comment="最大成长值，null表示无上限")

    discount_rate: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.00, comment="折扣率")
    free_shipping: Mapped[int] = mapped_column(SmallInteger, default=0, comment="包邮特权：0否/1是")
    priority_customer_service: Mapped[int] = mapped_column(SmallInteger, default=0, comment="优先客服：0否/1是")

    privileges: Mapped[str | None] = mapped_column(Text, comment="等级特权描述")


class UserPoints(Base):
    """用户积分变动记录表"""

    __tablename__ = "usr_points"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_change_type", "change_type"),
        Index("idx_change_time", "change_time"),
        {"comment": "用户积分变动记录表"},
    )

    points_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="积分ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    change_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="变动类型：1获得/2消费/3过期/4退回"
    )
    change_value: Mapped[int] = mapped_column(Integer, comment="变动值")
    before_value: Mapped[int] = mapped_column(Integer, comment="变动前积分")
    after_value: Mapped[int] = mapped_column(Integer, comment="变动后积分")

    source_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="来源类型：1购物/2签到/3活动/4兑换/5其他"
    )
    source_id: Mapped[str | None] = mapped_column(String(64), comment="来源ID")

    expire_time: Mapped[datetime | None] = mapped_column(comment="过期时间")
    remark: Mapped[str | None] = mapped_column(String(200), comment="备注")
    change_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="变动时间")
