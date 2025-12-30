"""
Product Domain Models for E-commerce Schema.

This module contains product-related tables including:
- Product categories and brands
- SPU (Standard Product Unit) and SKU (Stock Keeping Unit)
- Product attributes and images
- Price history
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
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, TimestampMixin, SoftDeleteMixin


class ProductCategory(Base, TimestampMixin, SoftDeleteMixin):
    """商品类目表"""

    __tablename__ = "prd_category"
    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        Index("idx_level", "level"),
        {"comment": "商品类目表"},
    )

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="类目ID")
    category_name: Mapped[str] = mapped_column(String(100), comment="类目名称")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父类目ID，0表示顶级")
    level: Mapped[int] = mapped_column(SmallInteger, comment="层级：1一级/2二级/3三级")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    icon_url: Mapped[str | None] = mapped_column(String(255), comment="图标URL")
    description: Mapped[str | None] = mapped_column(String(500), comment="类目描述")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class ProductBrand(Base, TimestampMixin, SoftDeleteMixin):
    """品牌表"""

    __tablename__ = "prd_brand"
    __table_args__ = (
        Index("idx_status", "status"),
        {"comment": "品牌表"},
    )

    brand_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="品牌ID")
    brand_name: Mapped[str] = mapped_column(String(100), comment="品牌名称")
    brand_name_en: Mapped[str | None] = mapped_column(String(100), comment="品牌英文名")
    logo_url: Mapped[str | None] = mapped_column(String(255), comment="品牌LOGO")
    description: Mapped[str | None] = mapped_column(Text, comment="品牌介绍")
    website: Mapped[str | None] = mapped_column(String(255), comment="官方网站")
    country: Mapped[str | None] = mapped_column(String(50), comment="品牌国家")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class Product(Base, TimestampMixin, SoftDeleteMixin):
    """商品SPU表 (Standard Product Unit)"""

    __tablename__ = "prd_product"
    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_brand_id", "brand_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        {"comment": "商品SPU表"},
    )

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="商品ID")
    product_no: Mapped[str] = mapped_column(String(32), unique=True, comment="商品编号")
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    category_id: Mapped[int] = mapped_column(BigInteger, comment="类目ID")
    brand_id: Mapped[int | None] = mapped_column(BigInteger, comment="品牌ID")

    main_image: Mapped[str] = mapped_column(String(255), comment="主图URL")
    subtitle: Mapped[str | None] = mapped_column(String(500), comment="副标题")
    keywords: Mapped[str | None] = mapped_column(String(500), comment="搜索关键词")

    min_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="最低价格")
    max_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="最高价格")

    sales_count: Mapped[int] = mapped_column(Integer, default=0, comment="销量")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, comment="收藏量")

    status: Mapped[int] = mapped_column(
        SmallInteger, default=0,
        comment="状态：0草稿/1待审核/2审核通过/3已上架/4已下架/5已删除"
    )
    shelf_time: Mapped[datetime | None] = mapped_column(comment="上架时间")
    off_shelf_time: Mapped[datetime | None] = mapped_column(comment="下架时间")


class ProductSKU(Base, TimestampMixin, SoftDeleteMixin):
    """商品SKU表 (Stock Keeping Unit)"""

    __tablename__ = "prd_sku"
    __table_args__ = (
        Index("idx_product_id", "product_id"),
        Index("idx_sku_no", "sku_no"),
        Index("idx_status", "status"),
        {"comment": "商品SKU表"},
    )

    sku_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="SKU ID")
    sku_no: Mapped[str] = mapped_column(String(32), unique=True, comment="SKU编号")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")

    sku_name: Mapped[str] = mapped_column(String(200), comment="SKU名称")
    sku_spec: Mapped[str | None] = mapped_column(String(500), comment="规格描述，如：红色/XL")

    market_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="市场价")
    sell_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="销售价")
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), comment="成本价")

    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="库存数量")
    available_stock: Mapped[int] = mapped_column(Integer, default=0, comment="可用库存")
    locked_stock: Mapped[int] = mapped_column(Integer, default=0, comment="锁定库存")

    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="重量(kg)")
    volume: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="体积(m³)")

    image_url: Mapped[str | None] = mapped_column(String(255), comment="SKU图片")
    barcode: Mapped[str | None] = mapped_column(String(50), comment="条形码")

    sales_count: Mapped[int] = mapped_column(Integer, default=0, comment="销量")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class ProductAttribute(Base, TimestampMixin):
    """商品属性表"""

    __tablename__ = "prd_attribute"
    __table_args__ = (
        Index("idx_category_id", "category_id"),
        {"comment": "商品属性表"},
    )

    attribute_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="属性ID")
    category_id: Mapped[int] = mapped_column(BigInteger, comment="类目ID")
    attribute_name: Mapped[str] = mapped_column(String(100), comment="属性名称，如：颜色/尺寸")
    attribute_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="属性类型：1销售属性(SKU规格)/2基本属性/3扩展属性"
    )
    input_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="录入方式：1手工录入/2单选/3多选"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_required: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否必填：0否/1是")


class ProductAttributeValue(Base, TimestampMixin):
    """属性值表"""

    __tablename__ = "prd_attribute_value"
    __table_args__ = (
        Index("idx_attribute_id", "attribute_id"),
        {"comment": "属性值表"},
    )

    value_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="属性值ID")
    attribute_id: Mapped[int] = mapped_column(BigInteger, comment="属性ID")
    value_name: Mapped[str] = mapped_column(String(100), comment="属性值名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")


class ProductSKUAttribute(Base):
    """SKU属性关联表"""

    __tablename__ = "prd_sku_attribute"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_attribute_id", "attribute_id"),
        {"comment": "SKU属性关联表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    attribute_id: Mapped[int] = mapped_column(BigInteger, comment="属性ID")
    value_id: Mapped[int] = mapped_column(BigInteger, comment="属性值ID")


class ProductImage(Base, TimestampMixin):
    """商品图片表"""

    __tablename__ = "prd_image"
    __table_args__ = (
        Index("idx_product_id", "product_id"),
        Index("idx_image_type", "image_type"),
        {"comment": "商品图片表"},
    )

    image_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="图片ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")
    image_url: Mapped[str] = mapped_column(String(255), comment="图片URL")
    image_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="图片类型：1主图/2轮播图/3详情图"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")


class ProductDescription(Base, TimestampMixin):
    """商品详情表"""

    __tablename__ = "prd_description"
    __table_args__ = (
        Index("idx_product_id", "product_id"),
        {"comment": "商品详情表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    product_id: Mapped[int] = mapped_column(BigInteger, unique=True, comment="商品ID")
    description: Mapped[str] = mapped_column(Text, comment="商品详情HTML")
    mobile_description: Mapped[str | None] = mapped_column(Text, comment="移动端详情HTML")
    parameters: Mapped[str | None] = mapped_column(Text, comment="商品参数JSON")
    packaging_list: Mapped[str | None] = mapped_column(Text, comment="包装清单")
    after_sales_service: Mapped[str | None] = mapped_column(Text, comment="售后服务")


class ProductPriceHistory(Base):
    """价格历史表"""

    __tablename__ = "prd_price_history"
    __table_args__ = (
        Index("idx_sku_id", "sku_id"),
        Index("idx_change_time", "change_time"),
        {"comment": "价格历史表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    old_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="原价格")
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="新价格")
    change_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="变更类型：1调价/2促销/3成本变动"
    )
    change_reason: Mapped[str | None] = mapped_column(String(500), comment="变更原因")
    change_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="变更时间")
    operator_id: Mapped[int | None] = mapped_column(BigInteger, comment="操作人ID")
