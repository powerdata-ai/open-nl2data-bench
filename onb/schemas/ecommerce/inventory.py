"""
Inventory and Supplier Domain Models for E-commerce Schema.

This module contains inventory and supplier-related tables including:
- Stock management and logs
- Stock allocation and reservation
- Supplier management
- Purchase orders
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
# Inventory Domain
# ============================================================================


class InventoryStock(Base, TimestampMixin):
    """库存主表"""

    __tablename__ = "inv_stock"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_warehouse_id", "warehouse_id"),
        {"comment": "库存主表"},
    )

    stock_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="库存ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    total_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="总库存")
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="可用库存")
    locked_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="锁定库存")
    allocated_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已分配库存")
    defective_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="残次品库存")

    safety_stock: Mapped[int] = mapped_column(Integer, default=0, comment="安全库存")
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, comment="再订货点")
    max_stock: Mapped[int] = mapped_column(Integer, default=0, comment="最大库存")

    last_in_time: Mapped[datetime | None] = mapped_column(comment="最后入库时间")
    last_out_time: Mapped[datetime | None] = mapped_column(comment="最后出库时间")


class InventoryStockLog(Base):
    """库存变动日志表"""

    __tablename__ = "inv_stock_log"
    __table_args__ = (
        Index("idx_stock_id", "stock_id"),
        Index("idx_sku_id", "sku_id"),
        Index("idx_log_time", "log_time"),
        Index("idx_change_type", "change_type"),
        {"comment": "库存变动日志表"},
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")
    stock_id: Mapped[int] = mapped_column(BigInteger, comment="库存ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    change_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="变动类型：1入库/2出库/3调拨/4盘点/5锁定/6解锁/7报损"
    )
    change_quantity: Mapped[int] = mapped_column(Integer, comment="变动数量")
    before_quantity: Mapped[int] = mapped_column(Integer, comment="变动前数量")
    after_quantity: Mapped[int] = mapped_column(Integer, comment="变动后数量")

    business_no: Mapped[str | None] = mapped_column(String(64), comment="业务单号")
    business_type: Mapped[int | None] = mapped_column(
        SmallInteger,
        comment="业务类型：1采购/2销售/3退货/4调拨/5盘点"
    )

    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")
    operator_id: Mapped[int | None] = mapped_column(BigInteger, comment="操作人ID")
    log_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="变动时间")


class InventoryAllocation(Base, TimestampMixin):
    """库存分配表"""

    __tablename__ = "inv_allocation"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_sku_id", "sku_id"),
        Index("idx_status", "status"),
        {"comment": "库存分配表"},
    )

    allocation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="分配ID")
    order_id: Mapped[int] = mapped_column(BigInteger, comment="订单ID")
    order_item_id: Mapped[int] = mapped_column(BigInteger, comment="订单明细ID")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    allocated_quantity: Mapped[int] = mapped_column(Integer, comment="分配数量")
    picked_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已拣货数量")
    shipped_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已发货数量")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待拣货/1拣货中/2已拣货/3已发货/4已取消"
    )
    allocation_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="分配时间")


class InventoryReservation(Base, TimestampMixin):
    """库存预占表"""

    __tablename__ = "inv_reservation"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_sku_id", "sku_id"),
        Index("idx_status", "status"),
        Index("idx_expire_time", "expire_time"),
        {"comment": "库存预占表"},
    )

    reservation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="预占ID")
    order_id: Mapped[int] = mapped_column(BigInteger, comment="订单ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    reserved_quantity: Mapped[int] = mapped_column(Integer, comment="预占数量")
    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0有效/1已取消/2已转为分配/3已过期"
    )

    reservation_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="预占时间")
    expire_time: Mapped[datetime] = mapped_column(comment="过期时间")
    release_time: Mapped[datetime | None] = mapped_column(comment="释放时间")


class InventoryAdjustment(Base, TimestampMixin):
    """库存调整表"""

    __tablename__ = "inv_adjustment"
    __table_args__ = (
        Index("idx_adjustment_no", "adjustment_no"),
        Index("idx_sku_id", "sku_id"),
        Index("idx_adjustment_time", "adjustment_time"),
        {"comment": "库存调整表"},
    )

    adjustment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="调整ID")
    adjustment_no: Mapped[str] = mapped_column(String(32), unique=True, comment="调整单号")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    adjustment_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="调整类型：1盘盈/2盘亏/3报损/4其他"
    )
    adjustment_quantity: Mapped[int] = mapped_column(Integer, comment="调整数量")
    before_quantity: Mapped[int] = mapped_column(Integer, comment="调整前数量")
    after_quantity: Mapped[int] = mapped_column(Integer, comment="调整后数量")

    reason: Mapped[str | None] = mapped_column(String(500), comment="调整原因")
    operator_id: Mapped[int] = mapped_column(BigInteger, comment="操作人ID")
    auditor_id: Mapped[int | None] = mapped_column(BigInteger, comment="审核人ID")

    adjustment_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="调整时间")
    audit_time: Mapped[datetime | None] = mapped_column(comment="审核时间")


class InventoryTransfer(Base, TimestampMixin):
    """库存调拨表"""

    __tablename__ = "inv_transfer"
    __table_args__ = (
        Index("idx_transfer_no", "transfer_no"),
        Index("idx_sku_id", "sku_id"),
        Index("idx_status", "status"),
        {"comment": "库存调拨表"},
    )

    transfer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="调拨ID")
    transfer_no: Mapped[str] = mapped_column(String(32), unique=True, comment="调拨单号")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    from_warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="调出仓库ID")
    to_warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="调入仓库ID")

    transfer_quantity: Mapped[int] = mapped_column(Integer, comment="调拨数量")
    actual_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="实际到货数量")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待审核/1已审核/2已出库/3在途/4已到货/5已取消"
    )

    applicant_id: Mapped[int] = mapped_column(BigInteger, comment="申请人ID")
    auditor_id: Mapped[int | None] = mapped_column(BigInteger, comment="审核人ID")

    apply_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="申请时间")
    audit_time: Mapped[datetime | None] = mapped_column(comment="审核时间")
    out_time: Mapped[datetime | None] = mapped_column(comment="出库时间")
    in_time: Mapped[datetime | None] = mapped_column(comment="入库时间")


class InventorySafetyStock(Base, TimestampMixin):
    """安全库存配置表"""

    __tablename__ = "inv_safety_stock"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_warehouse_id", "warehouse_id"),
        {"comment": "安全库存配置表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="仓库ID")

    safety_stock: Mapped[int] = mapped_column(Integer, comment="安全库存")
    reorder_point: Mapped[int] = mapped_column(Integer, comment="再订货点")
    max_stock: Mapped[int] = mapped_column(Integer, comment="最大库存")
    lead_time_days: Mapped[int] = mapped_column(Integer, comment="补货周期(天)")

    auto_purchase: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否自动采购：0否/1是")


# ============================================================================
# Supplier Domain
# ============================================================================


class Supplier(Base, TimestampMixin, SoftDeleteMixin):
    """供应商表"""

    __tablename__ = "sup_supplier"
    __table_args__ = (
        Index("idx_supplier_code", "supplier_code"),
        Index("idx_status", "status"),
        {"comment": "供应商表"},
    )

    supplier_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="供应商ID")
    supplier_code: Mapped[str] = mapped_column(String(32), unique=True, comment="供应商编码")
    supplier_name: Mapped[str] = mapped_column(String(200), comment="供应商名称")

    contact_person: Mapped[str | None] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[str | None] = mapped_column(String(20), comment="联系电话")
    contact_email: Mapped[str | None] = mapped_column(String(100), comment="联系邮箱")
    address: Mapped[str | None] = mapped_column(String(500), comment="地址")

    business_license: Mapped[str | None] = mapped_column(String(50), comment="营业执照号")
    tax_number: Mapped[str | None] = mapped_column(String(50), comment="税号")

    cooperation_start_date: Mapped[datetime | None] = mapped_column(comment="合作开始日期")
    credit_level: Mapped[str | None] = mapped_column(String(10), comment="信用等级：A/B/C/D")
    payment_term_days: Mapped[int] = mapped_column(Integer, default=30, comment="账期(天)")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用/2暂停合作")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")


class SupplierProduct(Base, TimestampMixin):
    """供应商商品关联表"""

    __tablename__ = "sup_product"
    __table_args__ = (
        Index("idx_supplier_id", "supplier_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "供应商商品关联表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    supplier_id: Mapped[int] = mapped_column(BigInteger, comment="供应商ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    supplier_sku_code: Mapped[str | None] = mapped_column(String(50), comment="供应商商品编码")
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="采购价")
    min_order_quantity: Mapped[int] = mapped_column(Integer, default=1, comment="最小起订量")
    lead_time_days: Mapped[int] = mapped_column(Integer, comment="供货周期(天)")

    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否默认供应商：0否/1是")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class PurchaseOrder(Base, TimestampMixin):
    """采购订单表"""

    __tablename__ = "sup_purchase_order"
    __table_args__ = (
        Index("idx_purchase_no", "purchase_no"),
        Index("idx_supplier_id", "supplier_id"),
        Index("idx_status", "status"),
        Index("idx_order_time", "order_time"),
        {"comment": "采购订单表"},
    )

    purchase_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="采购ID")
    purchase_no: Mapped[str] = mapped_column(String(32), unique=True, comment="采购单号")

    supplier_id: Mapped[int] = mapped_column(BigInteger, comment="供应商ID")
    warehouse_id: Mapped[int] = mapped_column(BigInteger, comment="入库仓库ID")

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="订单总金额")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="税额")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="优惠金额")
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="实付金额")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0待审核/1已审核/2部分到货/3全部到货/4已取消"
    )

    buyer_id: Mapped[int] = mapped_column(BigInteger, comment="采购员ID")
    auditor_id: Mapped[int | None] = mapped_column(BigInteger, comment="审核人ID")

    order_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="下单时间")
    audit_time: Mapped[datetime | None] = mapped_column(comment="审核时间")
    expected_arrival_time: Mapped[datetime | None] = mapped_column(comment="预计到货时间")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")


class PurchaseItem(Base):
    """采购订单明细表"""

    __tablename__ = "sup_purchase_item"
    __table_args__ = (
        Index("idx_purchase_id", "purchase_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "采购订单明细表"},
    )

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="明细ID")
    purchase_id: Mapped[int] = mapped_column(BigInteger, comment="采购ID")

    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    sku_name: Mapped[str] = mapped_column(String(200), comment="SKU名称")

    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="采购单价")
    order_quantity: Mapped[int] = mapped_column(Integer, comment="订购数量")
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="已收货数量")
    qualified_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="合格数量")

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="小计金额")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, comment="税率")


class PurchaseReceiving(Base, TimestampMixin):
    """采购收货记录表"""

    __tablename__ = "sup_receiving"
    __table_args__ = (
        Index("idx_receiving_no", "receiving_no"),
        Index("idx_purchase_id", "purchase_id"),
        Index("idx_receiving_time", "receiving_time"),
        {"comment": "采购收货记录表"},
    )

    receiving_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="收货ID")
    receiving_no: Mapped[str] = mapped_column(String(32), unique=True, comment="收货单号")

    purchase_id: Mapped[int] = mapped_column(BigInteger, comment="采购ID")
    item_id: Mapped[int] = mapped_column(BigInteger, comment="采购明细ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    received_quantity: Mapped[int] = mapped_column(Integer, comment="收货数量")
    qualified_quantity: Mapped[int] = mapped_column(Integer, comment="合格数量")
    defective_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="不合格数量")

    receiver_id: Mapped[int] = mapped_column(BigInteger, comment="收货人ID")
    receiving_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="收货时间")
    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")


class QualityCheck(Base, TimestampMixin):
    """质检记录表"""

    __tablename__ = "sup_quality_check"
    __table_args__ = (
        Index("idx_receiving_id", "receiving_id"),
        Index("idx_check_result", "check_result"),
        {"comment": "质检记录表"},
    )

    check_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="质检ID")
    receiving_id: Mapped[int] = mapped_column(BigInteger, comment="收货ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    check_quantity: Mapped[int] = mapped_column(Integer, comment="质检数量")
    qualified_quantity: Mapped[int] = mapped_column(Integer, comment="合格数量")
    defective_quantity: Mapped[int] = mapped_column(Integer, comment="不合格数量")

    check_result: Mapped[int] = mapped_column(
        SmallInteger,
        comment="质检结果：1合格/2不合格/3部分合格"
    )
    defect_reason: Mapped[str | None] = mapped_column(Text, comment="不合格原因")

    checker_id: Mapped[int] = mapped_column(BigInteger, comment="质检员ID")
    check_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="质检时间")
