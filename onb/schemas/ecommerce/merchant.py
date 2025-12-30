"""
Merchant and Store Domain Models for E-commerce Schema.

This module contains merchant and physical store-related tables including:
- Merchant management
- Store operations
- Merchant settlements
- Store inventory
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
# Merchant Domain
# ============================================================================


class Merchant(Base, TimestampMixin, SoftDeleteMixin):
    """商家表"""

    __tablename__ = "mch_merchant"
    __table_args__ = (
        Index("idx_merchant_code", "merchant_code"),
        Index("idx_status", "status"),
        {"comment": "商家表"},
    )

    merchant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="商家ID")
    merchant_code: Mapped[str] = mapped_column(String(32), unique=True, comment="商家编码")
    merchant_name: Mapped[str] = mapped_column(String(200), comment="商家名称")

    merchant_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="商家类型：1自营/2第三方/3品牌直营"
    )
    category_id: Mapped[int] = mapped_column(BigInteger, comment="经营类目ID")

    legal_person: Mapped[str] = mapped_column(String(50), comment="法人代表")
    business_license: Mapped[str] = mapped_column(String(50), comment="营业执照号")
    tax_number: Mapped[str] = mapped_column(String(50), comment="税号")

    contact_person: Mapped[str] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[str] = mapped_column(String(20), comment="联系电话")
    contact_email: Mapped[str | None] = mapped_column(String(100), comment="联系邮箱")

    settle_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="结算类型：1按天/2按周/3按月"
    )
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), comment="佣金比例")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待审核/1正常/2冻结/3关闭"
    )
    cooperation_start_date: Mapped[datetime | None] = mapped_column(comment="合作开始日期")


class MerchantCategory(Base, TimestampMixin):
    """商家经营类目表"""

    __tablename__ = "mch_category"
    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        {"comment": "商家经营类目表"},
    )

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="类目ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父类目ID")

    category_name: Mapped[str] = mapped_column(String(100), comment="类目名称")
    category_level: Mapped[int] = mapped_column(SmallInteger, comment="类目层级")

    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), comment="默认佣金比例")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class MerchantAccount(Base, TimestampMixin):
    """商家账户表"""

    __tablename__ = "mch_account"
    __table_args__ = (
        Index("idx_merchant_id", "merchant_id"),
        {"comment": "商家账户表"},
    )

    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="账户ID")
    merchant_id: Mapped[int] = mapped_column(BigInteger, unique=True, comment="商家ID")

    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="账户余额")
    frozen_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="冻结金额")
    total_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="累计收入")
    total_withdraw: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="累计提现")

    bank_name: Mapped[str | None] = mapped_column(String(100), comment="开户银行")
    bank_account: Mapped[str | None] = mapped_column(String(50), comment="银行账号")
    account_name: Mapped[str | None] = mapped_column(String(100), comment="账户名称")


class MerchantSettlement(Base, TimestampMixin):
    """商家结算表"""

    __tablename__ = "mch_settlement"
    __table_args__ = (
        Index("idx_settlement_no", "settlement_no"),
        Index("idx_merchant_id", "merchant_id"),
        Index("idx_settlement_date", "settlement_date"),
        Index("idx_status", "status"),
        {"comment": "商家结算表"},
    )

    settlement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="结算ID")
    settlement_no: Mapped[str] = mapped_column(String(32), unique=True, comment="结算单号")

    merchant_id: Mapped[int] = mapped_column(BigInteger, comment="商家ID")
    settlement_date: Mapped[datetime] = mapped_column(Date, comment="结算日期")

    order_count: Mapped[int] = mapped_column(Integer, comment="订单数量")
    order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="订单金额")
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="退款金额")

    commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="佣金金额")
    settlement_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="结算金额")
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="实付金额")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待确认/1已确认/2已结算/3已取消"
    )

    confirm_time: Mapped[datetime | None] = mapped_column(comment="确认时间")
    settle_time: Mapped[datetime | None] = mapped_column(comment="结算时间")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")


# ============================================================================
# Store Domain
# ============================================================================


class Store(Base, TimestampMixin, SoftDeleteMixin):
    """门店表"""

    __tablename__ = "mch_store"
    __table_args__ = (
        Index("idx_store_code", "store_code"),
        Index("idx_merchant_id", "merchant_id"),
        Index("idx_status", "status"),
        {"comment": "门店表"},
    )

    store_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="门店ID")
    store_code: Mapped[str] = mapped_column(String(32), unique=True, comment="门店编码")
    store_name: Mapped[str] = mapped_column(String(200), comment="门店名称")

    merchant_id: Mapped[int] = mapped_column(BigInteger, comment="所属商家ID")

    province: Mapped[str] = mapped_column(String(50), comment="省份")
    city: Mapped[str] = mapped_column(String(50), comment="城市")
    district: Mapped[str] = mapped_column(String(50), comment="区县")
    address: Mapped[str] = mapped_column(String(500), comment="详细地址")

    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="经度")
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="纬度")

    contact_person: Mapped[str] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[str] = mapped_column(String(20), comment="联系电话")

    business_hours: Mapped[str | None] = mapped_column(String(100), comment="营业时间")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0关闭/1营业/2装修")


class StoreStaff(Base, TimestampMixin, SoftDeleteMixin):
    """门店员工表"""

    __tablename__ = "mch_store_staff"
    __table_args__ = (
        Index("idx_store_id", "store_id"),
        Index("idx_staff_code", "staff_code"),
        Index("idx_status", "status"),
        {"comment": "门店员工表"},
    )

    staff_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="员工ID")
    store_id: Mapped[int] = mapped_column(BigInteger, comment="门店ID")
    staff_code: Mapped[str] = mapped_column(String(32), unique=True, comment="员工编码")

    staff_name: Mapped[str] = mapped_column(String(50), comment="姓名")
    mobile: Mapped[str] = mapped_column(String(20), comment="手机号")
    id_card: Mapped[str | None] = mapped_column(String(20), comment="身份证号")

    position: Mapped[str] = mapped_column(String(50), comment="职位")
    role_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="角色类型：1店长/2收银员/3导购/4仓管"
    )

    entry_date: Mapped[datetime] = mapped_column(comment="入职日期")
    leave_date: Mapped[datetime | None] = mapped_column(comment="离职日期")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0离职/1在职")


class StoreInventory(Base, TimestampMixin):
    """门店库存表"""

    __tablename__ = "mch_store_inventory"
    __table_args__ = (
        Index("idx_store_id", "store_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "门店库存表"},
    )

    inventory_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="库存ID")
    store_id: Mapped[int] = mapped_column(BigInteger, comment="门店ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    total_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="总库存")
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="可用库存")
    locked_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="锁定库存")

    min_stock: Mapped[int] = mapped_column(Integer, default=0, comment="最小库存")
    max_stock: Mapped[int] = mapped_column(Integer, default=0, comment="最大库存")

    last_in_time: Mapped[datetime | None] = mapped_column(comment="最后入库时间")
    last_out_time: Mapped[datetime | None] = mapped_column(comment="最后出库时间")


class StoreOrder(Base, TimestampMixin):
    """门店订单表"""

    __tablename__ = "mch_store_order"
    __table_args__ = (
        Index("idx_order_no", "order_no"),
        Index("idx_store_id", "store_id"),
        Index("idx_status", "status"),
        {"comment": "门店订单表"},
    )

    store_order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="门店订单ID")
    order_no: Mapped[str] = mapped_column(String(32), unique=True, comment="订单号")

    store_id: Mapped[int] = mapped_column(BigInteger, comment="门店ID")
    staff_id: Mapped[int] = mapped_column(BigInteger, comment="服务员工ID")

    user_id: Mapped[int | None] = mapped_column(BigInteger, comment="用户ID(会员)")
    member_no: Mapped[str | None] = mapped_column(String(32), comment="会员卡号")

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="订单总额")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="优惠金额")
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="实付金额")

    payment_method: Mapped[int] = mapped_column(
        SmallInteger,
        comment="支付方式：1现金/2支付宝/3微信/4刷卡/5会员卡"
    )

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待支付/1已支付/2已取消/3已退款"
    )

    order_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="下单时间")
    pay_time: Mapped[datetime | None] = mapped_column(comment="支付时间")
