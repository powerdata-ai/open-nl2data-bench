"""
Search and Recommendation Domain Models for E-commerce Schema.

This module contains search and recommendation-related tables including:
- Search queries and results
- Hot search keywords
- Product recommendations
- Search optimization
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, TimestampMixin


# ============================================================================
# Search Domain
# ============================================================================


class SearchQuery(Base, TimestampMixin):
    """搜索查询记录表"""

    __tablename__ = "sea_query"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_keyword", "keyword"),
        Index("idx_search_time", "search_time"),
        {"comment": "搜索查询记录表"},
    )

    query_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="查询ID")
    user_id: Mapped[int | None] = mapped_column(BigInteger, comment="用户ID")

    keyword: Mapped[str] = mapped_column(String(200), comment="搜索关键词")
    original_keyword: Mapped[str | None] = mapped_column(String(200), comment="原始关键词(纠错前)")

    result_count: Mapped[int] = mapped_column(Integer, default=0, comment="结果数量")
    click_count: Mapped[int] = mapped_column(Integer, default=0, comment="点击次数")
    clicked_product_ids: Mapped[str | None] = mapped_column(Text, comment="点击商品ID列表JSON")

    search_source: Mapped[int] = mapped_column(
        SmallInteger,
        comment="搜索来源：1搜索框/2推荐/3相关搜索/4店铺搜索"
    )
    device_type: Mapped[int | None] = mapped_column(
        SmallInteger,
        comment="设备类型：1PC/2iOS/3Android/4小程序"
    )

    search_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="搜索时间")


class SearchResult(Base):
    """搜索结果缓存表"""

    __tablename__ = "sea_result"
    __table_args__ = (
        Index("idx_query_id", "query_id"),
        Index("idx_product_id", "product_id"),
        {"comment": "搜索结果缓存表"},
    )

    result_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="结果ID")
    query_id: Mapped[int] = mapped_column(BigInteger, comment="查询ID")

    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")
    rank_score: Mapped[int] = mapped_column(Integer, comment="排序分数")
    rank_position: Mapped[int] = mapped_column(Integer, comment="排序位置")

    is_clicked: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否被点击：0否/1是")
    click_time: Mapped[datetime | None] = mapped_column(comment="点击时间")


class HotSearch(Base, TimestampMixin):
    """热搜词表"""

    __tablename__ = "sea_hot_search"
    __table_args__ = (
        Index("idx_keyword", "keyword"),
        Index("idx_search_count", "search_count"),
        Index("idx_stat_date", "stat_date"),
        {"comment": "热搜词表"},
    )

    hot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="热搜ID")
    keyword: Mapped[str] = mapped_column(String(200), comment="搜索关键词")

    search_count: Mapped[int] = mapped_column(Integer, default=0, comment="搜索次数")
    click_count: Mapped[int] = mapped_column(Integer, default=0, comment="点击次数")
    conversion_count: Mapped[int] = mapped_column(Integer, default=0, comment="转化次数")

    stat_date: Mapped[datetime] = mapped_column(comment="统计日期")
    rank_position: Mapped[int] = mapped_column(Integer, comment="排名位置")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0隐藏/1显示/2推荐")


class SearchSynonym(Base, TimestampMixin):
    """搜索同义词表"""

    __tablename__ = "sea_synonym"
    __table_args__ = (
        Index("idx_keyword", "keyword"),
        Index("idx_synonym", "synonym"),
        {"comment": "搜索同义词表"},
    )

    synonym_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="同义词ID")
    keyword: Mapped[str] = mapped_column(String(200), comment="关键词")
    synonym: Mapped[str] = mapped_column(String(200), comment="同义词")

    synonym_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="类型：1完全同义/2近义词/3纠错词"
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


class SearchFilter(Base, TimestampMixin):
    """搜索过滤器表"""

    __tablename__ = "sea_filter"
    __table_args__ = (
        Index("idx_filter_type", "filter_type"),
        {"comment": "搜索过滤器表"},
    )

    filter_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="过滤器ID")
    filter_name: Mapped[str] = mapped_column(String(100), comment="过滤器名称")

    filter_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="过滤器类型：1价格区间/2品牌/3分类/4属性"
    )
    filter_config: Mapped[str] = mapped_column(Text, comment="过滤器配置JSON")

    apply_scope: Mapped[int] = mapped_column(
        SmallInteger,
        comment="应用范围：1全局/2分类/3关键词"
    )
    target_ids: Mapped[str | None] = mapped_column(Text, comment="目标ID列表JSON")

    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用")


# ============================================================================
# Recommendation Domain
# ============================================================================


class RecommendStrategy(Base, TimestampMixin):
    """推荐策略表"""

    __tablename__ = "sea_recommend_strategy"
    __table_args__ = (
        Index("idx_strategy_code", "strategy_code"),
        Index("idx_status", "status"),
        {"comment": "推荐策略表"},
    )

    strategy_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="策略ID")
    strategy_code: Mapped[str] = mapped_column(String(50), unique=True, comment="策略编码")
    strategy_name: Mapped[str] = mapped_column(String(200), comment="策略名称")

    strategy_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="策略类型：1协同过滤/2内容推荐/3热门推荐/4新品推荐/5个性化推荐"
    )
    algorithm_type: Mapped[str] = mapped_column(String(50), comment="算法类型：CF/CB/DNN等")

    target_scene: Mapped[int] = mapped_column(
        SmallInteger,
        comment="目标场景：1首页/2详情页/3购物车/4搜索结果"
    )
    config_params: Mapped[str | None] = mapped_column(Text, comment="配置参数JSON")

    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0禁用/1启用/2测试")


class ProductRecommend(Base, TimestampMixin):
    """商品推荐记录表"""

    __tablename__ = "sea_product_recommend"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_product_id", "product_id"),
        Index("idx_strategy_id", "strategy_id"),
        Index("idx_recommend_time", "recommend_time"),
        {"comment": "商品推荐记录表"},
    )

    recommend_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="推荐ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品ID")

    strategy_id: Mapped[int] = mapped_column(BigInteger, comment="策略ID")
    recommend_score: Mapped[int] = mapped_column(Integer, comment="推荐分数")
    recommend_reason: Mapped[str | None] = mapped_column(String(500), comment="推荐理由")

    scene_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="推荐场景：1首页/2详情页/3购物车/4搜索结果"
    )
    position: Mapped[int] = mapped_column(Integer, comment="展示位置")

    is_shown: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否展示：0否/1是")
    is_clicked: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否点击：0否/1是")
    is_converted: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否转化：0否/1是")

    recommend_time: Mapped[datetime] = mapped_column(default=datetime.now, comment="推荐时间")
    click_time: Mapped[datetime | None] = mapped_column(comment="点击时间")


class UserRecommend(Base, TimestampMixin):
    """用户推荐偏好表"""

    __tablename__ = "sea_user_recommend"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        {"comment": "用户推荐偏好表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键ID")
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, comment="用户ID")

    preferred_categories: Mapped[str | None] = mapped_column(Text, comment="偏好类目JSON")
    preferred_brands: Mapped[str | None] = mapped_column(Text, comment="偏好品牌JSON")
    preferred_price_range: Mapped[str | None] = mapped_column(String(100), comment="偏好价格区间")

    click_rate: Mapped[int] = mapped_column(Integer, default=0, comment="推荐点击率(‰)")
    conversion_rate: Mapped[int] = mapped_column(Integer, default=0, comment="推荐转化率(‰)")

    last_recommend_time: Mapped[datetime | None] = mapped_column(comment="最后推荐时间")
    recommend_count: Mapped[int] = mapped_column(Integer, default=0, comment="累计推荐次数")
