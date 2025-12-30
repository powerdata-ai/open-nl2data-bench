"""
After-sales service domain schema definitions for e-commerce system.

This module contains supplementary after-sales service tables:
- Customer service tickets
- Knowledge base for common issues
- Quality inspection records

Note: Core after-sales tables (refund, logs, disputes, evaluations)
are defined in order.py module.

Total: 3 additional tables (7 total with order.py tables)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from onb.schemas.base import Base, SoftDeleteMixin, TimestampMixin


class AfterSalesTicket(Base, TimestampMixin):
    """
    售后工单表 - 客服工单管理.

    业务说明：
    - 用户提交售后问题，生成客服工单
    - 客服处理工单并记录处理结果
    - 用于售后问题跟踪和KPI统计
    """

    __tablename__ = "afs_ticket"
    __table_args__ = (
        Index("idx_ticket_no", "ticket_no"),
        Index("idx_user_id", "user_id"),
        Index("idx_refund_id", "refund_id"),
        Index("idx_ticket_status", "ticket_status"),
        {"comment": "售后工单表"},
    )

    # 主键
    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="工单ID")

    # 业务主键
    ticket_no: Mapped[str] = mapped_column(String(32), unique=True, comment="工单号")

    # 关联信息
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("ord_order_main.order_id"),
        nullable=True,
        comment="订单ID",
    )
    refund_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("ord_refund.refund_id"),
        nullable=True,
        comment="退款单ID",
    )

    # 工单类型
    ticket_type: Mapped[int] = mapped_column(
        SmallInteger,
        comment="工单类型：1订单咨询/2物流咨询/3退款问题/4商品质量/5其他",
    )
    ticket_category: Mapped[str] = mapped_column(
        String(100), comment="问题分类（如：发货慢、商品质量、退款退货等）"
    )

    # 问题描述
    ticket_title: Mapped[str] = mapped_column(String(200), comment="工单标题")
    ticket_desc: Mapped[str] = mapped_column(Text, comment="问题详细描述")
    ticket_images: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="问题图片（JSON数组）"
    )

    # 优先级
    priority_level: Mapped[int] = mapped_column(
        SmallInteger, comment="优先级：1低/2中/3高/4紧急"
    )

    # 工单状态
    ticket_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="工单状态：1待分配/2处理中/3待用户确认/4已解决/5已关闭",
    )

    # 处理信息
    assigned_agent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="分配客服ID"
    )
    assigned_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="分配时间"
    )
    first_response_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="首次响应时间"
    )
    resolve_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="解决时间"
    )

    # 处理结果
    solution_desc: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="解决方案描述"
    )
    internal_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="内部备注（用户不可见）"
    )

    # 满意度
    satisfaction_score: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, comment="满意度评分（1-5）"
    )
    satisfaction_comment: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="满意度评价"
    )

    # SLA指标（Service Level Agreement）
    sla_first_response_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="首次响应截止时间"
    )
    sla_resolution_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="问题解决截止时间"
    )
    sla_breached: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="是否违反SLA：0否/1是"
    )


class AfterSalesKnowledge(Base, TimestampMixin, SoftDeleteMixin):
    """
    售后知识库表 - 常见问题和解决方案.

    业务说明：
    - 维护常见售后问题的标准答案
    - 用于客服快速回复和自助服务
    - 支持分类管理和全文检索
    """

    __tablename__ = "afs_knowledge"
    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_knowledge_status", "knowledge_status"),
        {"comment": "售后知识库表"},
    )

    # 主键
    knowledge_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="知识ID"
    )

    # 分类
    category_id: Mapped[int] = mapped_column(BigInteger, comment="分类ID")
    category_name: Mapped[str] = mapped_column(String(100), comment="分类名称（冗余）")

    # 问题和答案
    question: Mapped[str] = mapped_column(String(500), comment="问题")
    answer: Mapped[str] = mapped_column(Text, comment="答案")

    # 关键词（用于搜索）
    keywords: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="关键词（逗号分隔）"
    )

    # 适用场景
    applicable_scenario: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="适用场景"
    )

    # 状态
    knowledge_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="状态：0禁用/1启用"
    )

    # 统计信息
    view_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="查看次数")
    helpful_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="有帮助次数")
    unhelpful_count: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="无帮助次数"
    )

    # 优先级和排序
    priority: Mapped[int] = mapped_column(SmallInteger, default=100, comment="优先级")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=100, comment="排序")

    # 维护信息
    author_id: Mapped[int] = mapped_column(BigInteger, comment="创建人ID")
    last_modifier_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="最后修改人ID"
    )


class AfterSalesQuality(Base, TimestampMixin):
    """
    售后质检表 - 客服质量检查记录.

    业务说明：
    - 对客服处理的工单进行质量检查
    - 记录质检结果和改进建议
    - 用于客服绩效评估和培训
    """

    __tablename__ = "afs_quality"
    __table_args__ = (
        Index("idx_ticket_id", "ticket_id"),
        Index("idx_agent_id", "agent_id"),
        Index("idx_inspector_id", "inspector_id"),
        Index("idx_quality_date", "quality_date"),
        {"comment": "售后质检表"},
    )

    # 主键
    quality_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="质检ID"
    )

    # 关联信息
    ticket_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("afs_ticket.ticket_id"), comment="工单ID"
    )
    agent_id: Mapped[int] = mapped_column(BigInteger, comment="客服ID")

    # 质检人
    inspector_id: Mapped[int] = mapped_column(BigInteger, comment="质检员ID")
    quality_date: Mapped[datetime] = mapped_column(DateTime, comment="质检日期")

    # 质检维度评分（每项1-5分）
    response_time_score: Mapped[int] = mapped_column(
        SmallInteger, comment="响应时效评分"
    )
    service_attitude_score: Mapped[int] = mapped_column(
        SmallInteger, comment="服务态度评分"
    )
    professional_score: Mapped[int] = mapped_column(
        SmallInteger, comment="专业能力评分"
    )
    problem_solving_score: Mapped[int] = mapped_column(
        SmallInteger, comment="问题解决评分"
    )
    communication_score: Mapped[int] = mapped_column(
        SmallInteger, comment="沟通技巧评分"
    )

    # 总分
    total_score: Mapped[int] = mapped_column(SmallInteger, comment="总分")

    # 质检结果
    quality_result: Mapped[int] = mapped_column(
        SmallInteger, comment="质检结果：1优秀/2良好/3合格/4不合格"
    )

    # 问题和建议
    problem_desc: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="存在问题描述"
    )
    improvement_advice: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="改进建议"
    )

    # 是否需要复训
    need_retraining: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="是否需要复训：0否/1是"
    )

    # 质检类型
    quality_type: Mapped[int] = mapped_column(
        SmallInteger, comment="质检类型：1随机质检/2专项质检/3投诉质检"
    )

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )
