"""
Operations and System Domain Models for E-commerce Schema.

This module contains operations and system-related tables including:
- CMS content management
- Customer service
- Data analytics
- System configuration
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


# ============================================================================
# Content Management System (CMS)
# ============================================================================


class CMSArticle(Base, TimestampMixin, SoftDeleteMixin):
    """CMS文章表"""

    __tablename__ = "cms_article"
    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_status", "status"),
        Index("idx_publish_time", "publish_time"),
        {"comment": "CMS文章表"},
    )

    article_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="文章ID")
    category_id: Mapped[int] = mapped_column(BigInteger, comment="分类ID")

    title: Mapped[str] = mapped_column(String(200), comment="文章标题")
    subtitle: Mapped[str | None] = mapped_column(String(500), comment="副标题")
    cover_image: Mapped[str | None] = mapped_column(String(255), comment="封面图")

    content: Mapped[str] = mapped_column(Text, comment="文章内容")
    summary: Mapped[str | None] = mapped_column(String(500), comment="摘要")

    author_id: Mapped[int] = mapped_column(BigInteger, comment="作者ID")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")
    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0草稿/1已发布/2已下线"
    )
    publish_time: Mapped[datetime | None] = mapped_column(comment="发布时间")


class CMSBanner(Base, TimestampMixin, SoftDeleteMixin):
    """轮播图表"""

    __tablename__ = "cms_banner"
    __table_args__ = (
        Index("idx_position", "position"),
        Index("idx_status", "status"),
        Index("idx_start_time", "start_time"),
        {"comment": "轮播图表"},
    )

    banner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="轮播图ID")
    banner_name: Mapped[str] = mapped_column(String(100), comment="名称")

    position: Mapped[int] = mapped_column(
        SmallInteger,
        comment="位置：1首页/2分类页/3详情页"
    )
    image_url: Mapped[str] = mapped_column(String(255), comment="图片URL")
    link_url: Mapped[str | None] = mapped_column(String(255), comment="跳转链接")
    link_type: Mapped[int | None] = mapped_column(
        SmallInteger,
        comment="链接类型：1商品/2活动/3文章/4外链"
    )

    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class CMSTopic(Base, TimestampMixin, SoftDeleteMixin):
    """专题活动表"""

    __tablename__ = "cms_topic"
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_start_time", "start_time"),
        {"comment": "专题活动表"},
    )

    topic_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="专题ID")
    topic_name: Mapped[str] = mapped_column(String(200), comment="专题名称")

    cover_image: Mapped[str] = mapped_column(String(255), comment="封面图")
    description: Mapped[str | None] = mapped_column(Text, comment="专题描述")
    content: Mapped[str] = mapped_column(Text, comment="专题内容HTML")

    product_ids: Mapped[str | None] = mapped_column(Text, comment="关联商品ID列表JSON")

    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")
    start_time: Mapped[datetime] = mapped_column(comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(comment="结束时间")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class CMSNavigation(Base, TimestampMixin):
    """导航菜单表"""

    __tablename__ = "cms_navigation"
    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        Index("idx_position", "position"),
        {"comment": "导航菜单表"},
    )

    nav_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="导航ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父导航ID")

    nav_name: Mapped[str] = mapped_column(String(100), comment="导航名称")
    nav_url: Mapped[str | None] = mapped_column(String(255), comment="导航链接")
    nav_icon: Mapped[str | None] = mapped_column(String(255), comment="图标")

    position: Mapped[int] = mapped_column(
        SmallInteger,
        comment="位置：1顶部导航/2底部导航/3侧边导航"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_external: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否外部链接：0否/1是")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


# ============================================================================
# Customer Service
# ============================================================================


class CustomerTicket(Base, TimestampMixin):
    """客服工单表"""

    __tablename__ = "cus_ticket"
    __table_args__ = (
        Index("idx_ticket_no", "ticket_no"),
        Index("idx_user_id", "user_id"),
        Index("idx_status", "status"),
        Index("idx_priority", "priority"),
        {"comment": "客服工单表"},
    )

    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="工单ID")
    ticket_no: Mapped[str] = mapped_column(String(32), unique=True, comment="工单号")

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    order_id: Mapped[int | None] = mapped_column(BigInteger, comment="关联订单ID")

    category: Mapped[int] = mapped_column(
        SmallInteger,
        comment="工单类别：1订单问题/2商品咨询/3投诉建议/4其他"
    )
    title: Mapped[str] = mapped_column(String(200), comment="工单标题")
    description: Mapped[str] = mapped_column(Text, comment="问题描述")

    priority: Mapped[int] = mapped_column(
        SmallInteger, default=1,
        comment="优先级：1低/2中/3高/4紧急"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待处理/1处理中/2待回复/3已解决/4已关闭"
    )

    assignee_id: Mapped[int | None] = mapped_column(BigInteger, comment="处理人ID")
    assign_time: Mapped[datetime | None] = mapped_column(comment="分配时间")
    resolve_time: Mapped[datetime | None] = mapped_column(comment="解决时间")
    close_time: Mapped[datetime | None] = mapped_column(comment="关闭时间")


class CustomerConversation(Base, TimestampMixin):
    """客服会话表"""

    __tablename__ = "cus_conversation"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_agent_id", "agent_id"),
        Index("idx_status", "status"),
        {"comment": "客服会话表"},
    )

    conversation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="会话ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    agent_id: Mapped[int | None] = mapped_column(BigInteger, comment="客服ID")

    channel: Mapped[int] = mapped_column(
        SmallInteger,
        comment="渠道：1在线客服/2电话/3邮件/4微信"
    )
    start_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="开始时间")
    end_time: Mapped[datetime | None] = mapped_column(comment="结束时间")

    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息数量")
    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0进行中/1已结束"
    )


class CustomerMessage(Base):
    """客服消息表"""

    __tablename__ = "cus_message"
    __table_args__ = (
        Index("idx_conversation_id", "conversation_id"),
        Index("idx_send_time", "send_time"),
        {"comment": "客服消息表"},
    )

    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="消息ID")
    conversation_id: Mapped[int] = mapped_column(BigInteger, comment="会话ID")

    sender_id: Mapped[int] = mapped_column(BigInteger, comment="发送者ID")
    sender_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="发送者类型：1用户/2客服/3系统"
    )

    message_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="消息类型：1文本/2图片/3语音/4文件"
    )
    content: Mapped[str] = mapped_column(Text, comment="消息内容")

    send_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="发送时间")


class CustomerSatisfaction(Base, TimestampMixin):
    """客服满意度评价表"""

    __tablename__ = "cus_satisfaction"
    __table_args__ = (
        Index("idx_ticket_id", "ticket_id"),
        Index("idx_conversation_id", "conversation_id"),
        Index("idx_rating", "rating"),
        {"comment": "客服满意度评价表"},
    )

    satisfaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="评价ID")
    ticket_id: Mapped[int | None] = mapped_column(BigInteger, comment="工单ID")
    conversation_id: Mapped[int | None] = mapped_column(BigInteger, comment="会话ID")

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    agent_id: Mapped[int] = mapped_column(BigInteger, comment="客服ID")

    rating: Mapped[int] = mapped_column(SmallInteger, comment="评分：1-5星")
    tags: Mapped[str | None] = mapped_column(String(500), comment="评价标签JSON")
    comment: Mapped[str | None] = mapped_column(Text, comment="评价内容")

    evaluate_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="评价时间")


# ============================================================================
# Data Analytics
# ============================================================================


class UserBehavior(Base):
    """用户行为分析表"""

    __tablename__ = "ana_user_behavior"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_behavior_type", "behavior_type"),
        Index("idx_behavior_time", "behavior_time"),
        {"comment": "用户行为分析表"},
    )

    behavior_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="行为ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    behavior_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="行为类型：1浏览/2搜索/3加购/4下单/5支付"
    )
    target_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="目标类型：1商品/2类目/3店铺"
    )
    target_id: Mapped[int] = mapped_column(BigInteger, comment="目标ID")

    session_id: Mapped[str | None] = mapped_column(String(64), comment="会话ID")
    device_type: Mapped[int | None] = mapped_column(
        SmallInteger,
        comment="设备类型：1PC/2iOS/3Android/4小程序"
    )

    behavior_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="行为时间")


class SalesDaily(Base):
    """日销售统计表"""

    __tablename__ = "ana_sales_daily"
    __table_args__ = (
        Index("idx_stat_date", "stat_date"),
        Index("idx_category_id", "category_id"),
        {"comment": "日销售统计表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    stat_date: Mapped[datetime] = mapped_column(Date, comment="统计日期")

    category_id: Mapped[int | None] = mapped_column(BigInteger, comment="类目ID，null表示全平台")

    order_count: Mapped[int] = mapped_column(Integer, default=0, comment="订单数")
    order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="订单金额")
    paid_order_count: Mapped[int] = mapped_column(Integer, default=0, comment="支付订单数")
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="支付金额")

    new_user_count: Mapped[int] = mapped_column(Integer, default=0, comment="新用户数")
    active_user_count: Mapped[int] = mapped_column(Integer, default=0, comment="活跃用户数")

    refund_order_count: Mapped[int] = mapped_column(Integer, default=0, comment="退款订单数")
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="退款金额")


class ProductView(Base):
    """商品浏览统计表"""

    __tablename__ = "ana_product_view"
    __table_args__ = (
        Index("idx_product_id", "product_id"),
        Index("idx_stat_date", "stat_date"),
        {"comment": "商品浏览统计表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")
    stat_date: Mapped[datetime] = mapped_column(Date, comment="统计日期")

    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")
    unique_visitor: Mapped[int] = mapped_column(Integer, default=0, comment="独立访客数")
    avg_duration: Mapped[int] = mapped_column(Integer, default=0, comment="平均停留时长(秒)")

    add_cart_count: Mapped[int] = mapped_column(Integer, default=0, comment="加购数")
    order_count: Mapped[int] = mapped_column(Integer, default=0, comment="下单数")
    conversion_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="转化率")


class ConversionFunnel(Base):
    """转化漏斗分析表"""

    __tablename__ = "ana_conversion"
    __table_args__ = (
        Index("idx_stat_date", "stat_date"),
        Index("idx_funnel_type", "funnel_type"),
        {"comment": "转化漏斗分析表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    stat_date: Mapped[datetime] = mapped_column(Date, comment="统计日期")

    funnel_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="漏斗类型：1全站/2类目/3活动"
    )
    target_id: Mapped[int | None] = mapped_column(BigInteger, comment="目标ID")

    visit_uv: Mapped[int] = mapped_column(Integer, default=0, comment="访问UV")
    product_view_uv: Mapped[int] = mapped_column(Integer, default=0, comment="商品浏览UV")
    add_cart_uv: Mapped[int] = mapped_column(Integer, default=0, comment="加购UV")
    order_uv: Mapped[int] = mapped_column(Integer, default=0, comment="下单UV")
    payment_uv: Mapped[int] = mapped_column(Integer, default=0, comment="支付UV")

    view_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="浏览率")
    add_cart_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="加购率")
    order_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="下单率")
    payment_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="支付率")


# ============================================================================
# System Configuration
# ============================================================================


class SystemConfig(Base, TimestampMixin):
    """系统配置表"""

    __tablename__ = "sys_config"
    __table_args__ = (
        Index("idx_config_key", "config_key"),
        Index("idx_config_group", "config_group"),
        {"comment": "系统配置表"},
    )

    config_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="配置ID")
    config_key: Mapped[str] = mapped_column(String(100), unique=True, comment="配置键")
    config_value: Mapped[str] = mapped_column(Text, comment="配置值")

    config_group: Mapped[str] = mapped_column(String(50), comment="配置分组")
    config_desc: Mapped[str | None] = mapped_column(String(500), comment="配置描述")
    value_type: Mapped[str] = mapped_column(String(20), default="string", comment="值类型：string/int/json")


class SystemDict(Base, TimestampMixin):
    """数据字典表"""

    __tablename__ = "sys_dict"
    __table_args__ = (
        Index("idx_dict_type", "dict_type"),
        Index("idx_dict_code", "dict_code"),
        {"comment": "数据字典表"},
    )

    dict_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="字典ID")
    dict_type: Mapped[str] = mapped_column(String(50), comment="字典类型")
    dict_code: Mapped[str] = mapped_column(String(50), comment="字典编码")
    dict_value: Mapped[str] = mapped_column(String(200), comment="字典值")

    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否默认：0否/1是")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class SystemRegion(Base):
    """地区表"""

    __tablename__ = "sys_region"
    __table_args__ = (
        Index("idx_parent_code", "parent_code"),
        Index("idx_region_code", "region_code"),
        Index("idx_level", "level"),
        {"comment": "地区表"},
    )

    region_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="地区ID")
    region_code: Mapped[str] = mapped_column(String(20), unique=True, comment="地区编码")
    region_name: Mapped[str] = mapped_column(String(100), comment="地区名称")

    parent_code: Mapped[str] = mapped_column(String(20), comment="父地区编码")
    level: Mapped[int] = mapped_column(SmallInteger, comment="层级：1省/2市/3区县")

    zip_code: Mapped[str | None] = mapped_column(String(10), comment="邮编")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")


class ExpressCompany(Base, TimestampMixin):
    """快递公司配置表"""

    __tablename__ = "sys_express"
    __table_args__ = (
        Index("idx_company_code", "company_code"),
        {"comment": "快递公司配置表"},
    )

    company_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="公司ID")
    company_code: Mapped[str] = mapped_column(String(32), unique=True, comment="公司编码")
    company_name: Mapped[str] = mapped_column(String(100), comment="公司名称")

    company_website: Mapped[str | None] = mapped_column(String(255), comment="官网")
    phone: Mapped[str | None] = mapped_column(String(50), comment="客服电话")

    api_type: Mapped[int | None] = mapped_column(
        SmallInteger,
        comment="API类型：1快递鸟/2快递100/3自建"
    )
    api_config: Mapped[str | None] = mapped_column(Text, comment="API配置JSON")

    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class NotificationTemplate(Base, TimestampMixin):
    """通知模板表"""

    __tablename__ = "sys_notification"
    __table_args__ = (
        Index("idx_template_code", "template_code"),
        Index("idx_channel", "channel"),
        {"comment": "通知模板表"},
    )

    template_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="模板ID")
    template_code: Mapped[str] = mapped_column(String(50), unique=True, comment="模板编码")
    template_name: Mapped[str] = mapped_column(String(200), comment="模板名称")

    channel: Mapped[int] = mapped_column(
        SmallInteger,
        comment="通知渠道：1站内信/2短信/3邮件/4推送"
    )
    title: Mapped[str | None] = mapped_column(String(200), comment="标题模板")
    content: Mapped[str] = mapped_column(Text, comment="内容模板")

    variables: Mapped[str | None] = mapped_column(String(500), comment="变量说明JSON")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")
