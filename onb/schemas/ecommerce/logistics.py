"""
Logistics domain schema definitions for e-commerce system.

This module contains all logistics-related tables:
- Warehouse and inventory management
- Logistics company configuration
- Shipping orders and tracking
- Delivery routes and packages
- Return logistics

Total: 10 tables
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


class Warehouse(Base, TimestampMixin, SoftDeleteMixin):
    """
    仓库表 - 仓库基础信息.

    业务说明：
    - 管理全国各地的仓库信息
    - 支持多仓库管理和就近发货
    """

    __tablename__ = "log_warehouse"
    __table_args__ = (
        Index("idx_warehouse_code", "warehouse_code"),
        {"comment": "仓库表"},
    )

    # 主键
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="仓库ID"
    )

    # 仓库信息
    warehouse_code: Mapped[str] = mapped_column(
        String(50), unique=True, comment="仓库编码"
    )
    warehouse_name: Mapped[str] = mapped_column(String(100), comment="仓库名称")
    warehouse_type: Mapped[int] = mapped_column(
        SmallInteger, comment="仓库类型：1自营仓/2第三方仓/3前置仓"
    )

    # 地址信息
    province: Mapped[str] = mapped_column(String(50), comment="省份")
    city: Mapped[str] = mapped_column(String(50), comment="城市")
    district: Mapped[str] = mapped_column(String(50), comment="区/县")
    address: Mapped[str] = mapped_column(String(200), comment="详细地址")

    # 联系信息
    contact_name: Mapped[str] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[str] = mapped_column(String(20), comment="联系电话")

    # 状态
    warehouse_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="仓库状态：0停用/1启用/2维护中"
    )

    # 容量信息
    total_area: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="总面积（平方米）"
    )
    usable_area: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="可用面积（平方米）"
    )


class Inventory(Base, TimestampMixin):
    """
    库存表 - 商品库存信息.

    业务说明：
    - 记录每个仓库中每个SKU的库存数量
    - 支持库存扣减、库存冻结等操作
    """

    __tablename__ = "log_inventory"
    __table_args__ = (
        Index("idx_warehouse_sku", "warehouse_id", "sku_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "库存表"},
    )

    # 主键
    inventory_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="库存ID"
    )

    # 关联信息
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_warehouse.warehouse_id"), comment="仓库ID"
    )
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    # 库存数量
    available_stock: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="可用库存"
    )
    frozen_stock: Mapped[int] = mapped_column(BigInteger, default=0, comment="冻结库存")
    in_transit_stock: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="在途库存"
    )

    # 安全库存
    safety_stock: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="安全库存（预警阈值）"
    )

    # 版本号（乐观锁）
    version: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="版本号（防止并发修改）"
    )


class LogisticsCompany(Base, TimestampMixin, SoftDeleteMixin):
    """
    物流公司表 - 物流公司基础信息.

    业务说明：
    - 管理合作的物流公司信息
    - 配置物流公司的接口信息
    """

    __tablename__ = "log_logistics_company"
    __table_args__ = (
        Index("idx_company_code", "company_code"),
        {"comment": "物流公司表"},
    )

    # 主键
    company_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="物流公司ID"
    )

    # 公司信息
    company_code: Mapped[str] = mapped_column(
        String(50), unique=True, comment="物流公司编码"
    )
    company_name: Mapped[str] = mapped_column(String(100), comment="物流公司名称")

    # API配置
    api_url: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="物流查询API地址"
    )
    api_key: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="API密钥（加密存储）"
    )

    # 服务范围
    service_type: Mapped[int] = mapped_column(
        SmallInteger, comment="服务类型：1快递/2物流/3同城配送"
    )
    coverage_area: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="覆盖区域（JSON数组）"
    )

    # 费率
    base_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="首重费用"
    )
    additional_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="续重费用"
    )

    # 状态
    company_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="状态：0停用/1启用"
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, default=100, comment="排序"
    )


class ShippingTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """
    运费模板表 - 配置不同地区的运费规则.

    业务说明：
    - 支持按地区设置不同的运费规则
    - 支持首重、续重、免邮等配置
    """

    __tablename__ = "log_shipping_template"
    __table_args__ = (Index("idx_template_name", "template_name"), {"comment": "运费模板表"})

    # 主键
    template_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="模板ID"
    )

    # 模板信息
    template_name: Mapped[str] = mapped_column(String(100), comment="模板名称")
    template_type: Mapped[int] = mapped_column(
        SmallInteger, comment="计费方式：1按件数/2按重量/3按体积"
    )

    # 默认运费
    default_first_unit: Mapped[int] = mapped_column(BigInteger, comment="首件/首重/首体积")
    default_first_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="首费"
    )
    default_additional_unit: Mapped[int] = mapped_column(
        BigInteger, comment="续件/续重/续体积"
    )
    default_additional_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="续费"
    )

    # 免邮规则
    free_shipping_type: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="免邮类型：0不免邮/1满金额免邮/2满件数免邮"
    )
    free_shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="免邮金额"
    )
    free_shipping_count: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="免邮件数"
    )

    # 状态
    template_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="状态：0停用/1启用"
    )


class ShippingOrder(Base, TimestampMixin):
    """
    发货单表 - 订单发货记录.

    业务说明：
    - 一个订单可能有多个发货单（部分发货）
    - 记录发货的仓库、物流公司等信息
    """

    __tablename__ = "log_shipping_order"
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_shipping_no", "shipping_no"),
        Index("idx_tracking_no", "tracking_no"),
        {"comment": "发货单表"},
    )

    # 主键
    shipping_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="发货单ID"
    )

    # 业务主键
    shipping_no: Mapped[str] = mapped_column(
        String(32), unique=True, comment="发货单号"
    )

    # 关联信息
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_main.order_id"), comment="订单ID"
    )
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_warehouse.warehouse_id"), comment="发货仓库ID"
    )

    # 物流信息
    logistics_company_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("log_logistics_company.company_id"),
        comment="物流公司ID",
    )
    tracking_no: Mapped[str] = mapped_column(String(50), comment="物流单号")

    # 收货人信息（快照）
    receiver_name: Mapped[str] = mapped_column(String(50), comment="收货人姓名")
    receiver_phone: Mapped[str] = mapped_column(String(20), comment="收货人电话")
    receiver_province: Mapped[str] = mapped_column(String(50), comment="收货省份")
    receiver_city: Mapped[str] = mapped_column(String(50), comment="收货城市")
    receiver_district: Mapped[str] = mapped_column(String(50), comment="收货区县")
    receiver_address: Mapped[str] = mapped_column(String(500), comment="收货详细地址")

    # 发货状态
    shipping_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="发货状态：1待发货/2已发货/3运输中/4派送中/5已签收/6退回",
    )

    # 时间信息
    ship_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="发货时间"
    )
    delivery_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="签收时间"
    )

    # 备注
    shipping_remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="发货备注"
    )


class ShippingItem(Base, TimestampMixin):
    """
    发货明细表 - 发货单的商品明细.

    业务说明：
    - 记录每个发货单中包含的商品信息
    - 用于库存出库和签收核对
    """

    __tablename__ = "log_shipping_item"
    __table_args__ = (
        Index("idx_shipping_id", "shipping_id"),
        Index("idx_sku_id", "sku_id"),
        {"comment": "发货明细表"},
    )

    # 主键
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="明细ID")

    # 关联信息
    shipping_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_shipping_order.shipping_id"), comment="发货单ID"
    )
    order_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_order_item.item_id"), comment="订单明细ID"
    )
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")

    # 商品信息（快照）
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    sku_name: Mapped[str] = mapped_column(String(200), comment="SKU名称")

    # 数量
    shipping_quantity: Mapped[int] = mapped_column(SmallInteger, comment="发货数量")
    received_quantity: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="签收数量"
    )


class TrackingInfo(Base, TimestampMixin):
    """
    物流跟踪表 - 记录物流轨迹信息.

    业务说明：
    - 定时从物流公司API拉取物流轨迹
    - 用于订单物流跟踪展示
    """

    __tablename__ = "log_tracking_info"
    __table_args__ = (
        Index("idx_shipping_id", "shipping_id"),
        Index("idx_tracking_time", "tracking_time"),
        {"comment": "物流跟踪表"},
    )

    # 主键
    tracking_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="跟踪ID"
    )

    # 关联信息
    shipping_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_shipping_order.shipping_id"), comment="发货单ID"
    )

    # 轨迹信息
    tracking_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="物流状态：1已揽收/2运输中/3到达派送城市/4派送中/5已签收/6异常",
    )
    tracking_location: Mapped[str] = mapped_column(String(200), comment="所在地")
    tracking_desc: Mapped[str] = mapped_column(String(500), comment="轨迹描述")

    # 时间
    tracking_time: Mapped[datetime] = mapped_column(DateTime, comment="轨迹时间")

    # 操作人（如快递员）
    operator: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="操作人"
    )


class DeliveryRoute(Base, TimestampMixin):
    """
    配送路线表 - 同城配送的配送路线.

    业务说明：
    - 用于同城配送的路线规划
    - 记录配送员和配送路线信息
    """

    __tablename__ = "log_delivery_route"
    __table_args__ = (
        Index("idx_route_no", "route_no"),
        Index("idx_courier_id", "courier_id"),
        Index("idx_delivery_date", "delivery_date"),
        {"comment": "配送路线表"},
    )

    # 主键
    route_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="路线ID")

    # 路线号
    route_no: Mapped[str] = mapped_column(String(32), unique=True, comment="路线号")

    # 配送员
    courier_id: Mapped[int] = mapped_column(BigInteger, comment="配送员ID")
    courier_name: Mapped[str] = mapped_column(String(50), comment="配送员姓名")
    courier_phone: Mapped[str] = mapped_column(String(20), comment="配送员电话")

    # 配送信息
    delivery_date: Mapped[datetime] = mapped_column(DateTime, comment="配送日期")
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_warehouse.warehouse_id"), comment="出发仓库ID"
    )

    # 路线状态
    route_status: Mapped[int] = mapped_column(
        SmallInteger, comment="路线状态：1待配送/2配送中/3已完成/4已取消"
    )

    # 订单数量
    total_orders: Mapped[int] = mapped_column(SmallInteger, comment="总订单数")
    completed_orders: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="已完成订单数"
    )

    # 时间
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="出发时间"
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )


class ReturnShipping(Base, TimestampMixin):
    """
    退货物流表 - 退货的物流信息.

    业务说明：
    - 记录退货退款时的退货物流信息
    - 用于跟踪退货商品的物流状态
    """

    __tablename__ = "log_return_shipping"
    __table_args__ = (
        Index("idx_refund_id", "refund_id"),
        Index("idx_return_tracking_no", "return_tracking_no"),
        {"comment": "退货物流表"},
    )

    # 主键
    return_shipping_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="退货物流ID"
    )

    # 关联信息
    refund_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ord_refund.refund_id"), comment="退款单ID"
    )

    # 物流信息
    logistics_company_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("log_logistics_company.company_id"),
        comment="物流公司ID",
    )
    return_tracking_no: Mapped[str] = mapped_column(String(50), comment="退货物流单号")

    # 寄件人信息
    sender_name: Mapped[str] = mapped_column(String(50), comment="寄件人姓名")
    sender_phone: Mapped[str] = mapped_column(String(20), comment="寄件人电话")
    sender_address: Mapped[str] = mapped_column(String(500), comment="寄件地址")

    # 收件地址（退货地址）
    return_warehouse_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("log_warehouse.warehouse_id"),
        nullable=True,
        comment="退货仓库ID",
    )
    return_address: Mapped[str] = mapped_column(String(500), comment="退货地址")

    # 状态
    return_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="退货状态：1待寄回/2已寄回/3运输中/4已入库/5异常",
    )

    # 时间
    ship_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="寄出时间"
    )
    receive_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="入库时间"
    )


class PackageInfo(Base, TimestampMixin):
    """
    包裹信息表 - 记录包裹的详细信息.

    业务说明：
    - 记录每个包裹的重量、体积等物理信息
    - 用于运费计算和物流追踪
    """

    __tablename__ = "log_package_info"
    __table_args__ = (
        Index("idx_shipping_id", "shipping_id"),
        Index("idx_package_no", "package_no"),
        {"comment": "包裹信息表"},
    )

    # 主键
    package_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="包裹ID"
    )

    # 包裹号
    package_no: Mapped[str] = mapped_column(String(32), unique=True, comment="包裹号")

    # 关联信息
    shipping_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("log_shipping_order.shipping_id"), comment="发货单ID"
    )

    # 包裹信息
    package_weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), comment="包裹重量（kg）"
    )
    package_length: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="包裹长度（cm）"
    )
    package_width: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="包裹宽度（cm）"
    )
    package_height: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="包裹高度（cm）"
    )
    package_volume: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), comment="包裹体积（立方米）"
    )

    # 包裹类型
    package_type: Mapped[int] = mapped_column(
        SmallInteger, comment="包裹类型：1标准包裹/2大件/3易碎品/4特殊物品"
    )

    # 打包信息
    packer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="打包人ID"
    )
    pack_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="打包时间"
    )

    # 备注
    package_remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="包裹备注"
    )
