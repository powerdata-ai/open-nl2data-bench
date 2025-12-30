"""
Payment domain schema definitions for e-commerce system.

This module contains all payment-related tables:
- Payment order management
- Payment channel configuration
- Payment and refund flows
- Account balance and logs
- Payment callbacks and settlements

Total: 8 tables
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


class PaymentOrder(Base, TimestampMixin):
    """
    支付订单表 - 支付系统的核心表.

    业务说明：
    - 每次支付请求生成一条支付订单记录
    - 支付订单与业务订单解耦，一对多关系
    - 记录支付全流程状态
    """

    __tablename__ = "pay_payment_order"
    __table_args__ = (
        Index("idx_payment_no", "payment_no"),
        Index("idx_business_no", "business_no"),
        Index("idx_user_id", "user_id"),
        Index("idx_payment_status", "payment_status"),
        {"comment": "支付订单表"},
    )

    # 主键
    payment_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="支付ID"
    )

    # 业务主键
    payment_no: Mapped[str] = mapped_column(
        String(32), unique=True, comment="支付单号（内部）"
    )
    business_no: Mapped[str] = mapped_column(String(32), comment="业务订单号（如订单号）")
    business_type: Mapped[int] = mapped_column(
        SmallInteger, comment="业务类型：1订单支付/2充值/3保证金/4其他"
    )

    # 用户信息
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    # 金额信息
    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="支付金额"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="实际到账金额（扣除手续费后）"
    )
    fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="手续费"
    )

    # 支付渠道
    channel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pay_payment_channel.channel_id"), comment="支付渠道ID"
    )
    channel_code: Mapped[str] = mapped_column(String(50), comment="渠道编码（冗余）")

    # 支付方式
    payment_method: Mapped[int] = mapped_column(
        SmallInteger,
        comment="支付方式：1支付宝/2微信/3银行卡/4余额/5货到付款/6组合支付",
    )

    # 第三方支付信息
    trade_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="第三方支付流水号"
    )

    # 状态
    payment_status: Mapped[int] = mapped_column(
        SmallInteger,
        comment="支付状态：0待支付/1支付中/2已支付/3支付失败/4已关闭/5已退款",
    )

    # 时间信息
    request_time: Mapped[datetime] = mapped_column(DateTime, comment="发起支付时间")
    payment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="支付完成时间"
    )
    close_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="关闭时间"
    )

    # 过期时间
    expire_time: Mapped[datetime] = mapped_column(DateTime, comment="支付过期时间")

    # 其他信息
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="客户端IP"
    )
    device_info: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="设备信息"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )


class PaymentChannel(Base, TimestampMixin, SoftDeleteMixin):
    """
    支付渠道表 - 配置各种支付渠道.

    业务说明：
    - 记录支付宝、微信等第三方支付渠道的配置信息
    - 支持启用/禁用渠道
    """

    __tablename__ = "pay_payment_channel"
    __table_args__ = (
        Index("idx_channel_code", "channel_code"),
        {"comment": "支付渠道表"},
    )

    # 主键
    channel_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="渠道ID"
    )

    # 渠道信息
    channel_code: Mapped[str] = mapped_column(
        String(50), unique=True, comment="渠道编码（如：ALIPAY、WECHAT）"
    )
    channel_name: Mapped[str] = mapped_column(String(100), comment="渠道名称")
    channel_type: Mapped[int] = mapped_column(
        SmallInteger, comment="渠道类型：1第三方支付/2银行直连/3账户余额"
    )

    # 配置信息（加密存储）
    app_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="应用ID"
    )
    merchant_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="商户号"
    )
    api_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="API配置（JSON加密）"
    )

    # 费率配置
    fee_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0"), comment="手续费费率（如0.006表示0.6%）"
    )
    min_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="最低手续费"
    )
    max_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), comment="最高手续费"
    )

    # 限额配置
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.01"), comment="最小支付金额"
    )
    max_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("999999.99"), comment="最大支付金额"
    )

    # 状态
    channel_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="渠道状态：0禁用/1启用/2维护中"
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, default=100, comment="排序（数字越小越靠前）"
    )


class PaymentFlow(Base, TimestampMixin):
    """
    支付流水表 - 记录每一笔支付流水.

    业务说明：
    - 详细记录每次支付请求和响应
    - 用于对账和异常排查
    """

    __tablename__ = "pay_payment_flow"
    __table_args__ = (
        Index("idx_payment_id", "payment_id"),
        Index("idx_flow_no", "flow_no"),
        Index("idx_created_at", "created_at"),
        {"comment": "支付流水表"},
    )

    # 主键
    flow_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="流水ID")

    # 流水号
    flow_no: Mapped[str] = mapped_column(String(32), unique=True, comment="流水号")

    # 关联信息
    payment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pay_payment_order.payment_id"), comment="支付订单ID"
    )

    # 流水类型
    flow_type: Mapped[int] = mapped_column(
        SmallInteger, comment="流水类型：1支付请求/2支付回调/3查询/4退款/5退款回调"
    )

    # 金额
    flow_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="流水金额")

    # 第三方信息
    channel_flow_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="渠道流水号"
    )
    channel_request: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="请求内容（JSON）"
    )
    channel_response: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="响应内容（JSON）"
    )

    # 状态
    flow_status: Mapped[int] = mapped_column(
        SmallInteger, comment="流水状态：0处理中/1成功/2失败"
    )

    # 错误信息
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="错误码"
    )
    error_msg: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="错误信息"
    )


class RefundFlow(Base, TimestampMixin):
    """
    退款流水表 - 记录退款流水.

    业务说明：
    - 记录退款请求和处理结果
    - 支持部分退款和多次退款
    """

    __tablename__ = "pay_refund_flow"
    __table_args__ = (
        Index("idx_payment_id", "payment_id"),
        Index("idx_refund_no", "refund_no"),
        Index("idx_created_at", "created_at"),
        {"comment": "退款流水表"},
    )

    # 主键
    refund_flow_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="退款流水ID"
    )

    # 退款单号
    refund_no: Mapped[str] = mapped_column(String(32), unique=True, comment="退款单号")

    # 关联信息
    payment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pay_payment_order.payment_id"), comment="原支付订单ID"
    )
    business_refund_no: Mapped[str] = mapped_column(
        String(32), comment="业务退款单号（如订单退款单号）"
    )

    # 退款金额
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="退款金额")
    actual_refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="实际退款金额"
    )

    # 第三方退款信息
    channel_refund_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="渠道退款流水号"
    )

    # 状态
    refund_status: Mapped[int] = mapped_column(
        SmallInteger, comment="退款状态：0退款中/1退款成功/2退款失败"
    )

    # 时间
    refund_request_time: Mapped[datetime] = mapped_column(
        DateTime, comment="退款请求时间"
    )
    refund_success_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="退款成功时间"
    )

    # 退款原因
    refund_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="退款原因"
    )


class AccountBalance(Base, TimestampMixin):
    """
    账户余额表 - 用户账户余额.

    业务说明：
    - 记录用户的账户余额
    - 支持充值、消费、提现等操作
    """

    __tablename__ = "pay_account_balance"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        {"comment": "账户余额表"},
    )

    # 主键
    account_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="账户ID"
    )

    # 用户信息
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, comment="用户ID")

    # 余额信息
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="可用余额"
    )
    frozen_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="冻结余额"
    )
    total_recharge: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="累计充值金额"
    )
    total_consume: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="累计消费金额"
    )
    total_withdraw: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), comment="累计提现金额"
    )

    # 状态
    account_status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="账户状态：0冻结/1正常/2注销"
    )

    # 版本号（用于乐观锁）
    version: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="版本号（防止并发修改）"
    )


class BalanceLog(Base):
    """
    余额变动日志表 - 记录余额的每次变动.

    业务说明：
    - 详细记录每一笔余额变动
    - 用于账户流水查询和对账
    """

    __tablename__ = "pay_balance_log"
    __table_args__ = (
        Index("idx_account_id", "account_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
        {"comment": "余额变动日志表"},
    )

    # 主键
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")

    # 关联信息
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pay_account_balance.account_id"), comment="账户ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID（冗余）")

    # 业务关联
    business_no: Mapped[str] = mapped_column(String(32), comment="业务单号")
    business_type: Mapped[int] = mapped_column(
        SmallInteger, comment="业务类型：1充值/2消费/3退款/4提现/5冻结/6解冻"
    )

    # 金额变动
    change_type: Mapped[int] = mapped_column(
        SmallInteger, comment="变动类型：1增加/2减少"
    )
    change_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="变动金额")

    # 余额快照
    before_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="变动前余额"
    )
    after_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="变动后余额")

    # 说明
    change_desc: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="变动说明"
    )

    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )


class PaymentCallback(Base, TimestampMixin):
    """
    支付回调记录表 - 记录第三方支付的回调信息.

    业务说明：
    - 记录第三方支付平台的异步回调
    - 用于幂等性校验和异常排查
    """

    __tablename__ = "pay_payment_callback"
    __table_args__ = (
        Index("idx_payment_id", "payment_id"),
        Index("idx_callback_time", "callback_time"),
        {"comment": "支付回调记录表"},
    )

    # 主键
    callback_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="回调ID"
    )

    # 关联信息
    payment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("pay_payment_order.payment_id"),
        nullable=True,
        comment="支付订单ID（可能回调时还未匹配到订单）",
    )

    # 回调类型
    callback_type: Mapped[int] = mapped_column(
        SmallInteger, comment="回调类型：1支付回调/2退款回调"
    )

    # 回调内容
    channel_code: Mapped[str] = mapped_column(String(50), comment="渠道编码")
    callback_data: Mapped[str] = mapped_column(Text, comment="回调原始数据（JSON）")

    # 处理状态
    handle_status: Mapped[int] = mapped_column(
        SmallInteger, comment="处理状态：0待处理/1处理成功/2处理失败"
    )
    handle_times: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="处理次数"
    )

    # 验签结果
    sign_verify: Mapped[int] = mapped_column(
        SmallInteger, comment="验签结果：0未验签/1验签成功/2验签失败"
    )

    # 时间
    callback_time: Mapped[datetime] = mapped_column(DateTime, comment="回调时间")
    handle_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="处理完成时间"
    )

    # 错误信息
    error_msg: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="错误信息"
    )


class SettlementRecord(Base, TimestampMixin):
    """
    结算记录表 - 商户结算记录.

    业务说明：
    - 记录与第三方支付渠道的结算信息
    - 按周期（日/周/月）进行结算
    """

    __tablename__ = "pay_settlement_record"
    __table_args__ = (
        Index("idx_settlement_date", "settlement_date"),
        Index("idx_channel_id", "channel_id"),
        {"comment": "结算记录表"},
    )

    # 主键
    settlement_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="结算ID"
    )

    # 结算单号
    settlement_no: Mapped[str] = mapped_column(
        String(32), unique=True, comment="结算单号"
    )

    # 渠道信息
    channel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pay_payment_channel.channel_id"), comment="支付渠道ID"
    )

    # 结算周期
    settlement_cycle: Mapped[int] = mapped_column(
        SmallInteger, comment="结算周期：1日结/2周结/3月结"
    )
    settlement_date: Mapped[datetime] = mapped_column(DateTime, comment="结算日期")
    start_time: Mapped[datetime] = mapped_column(DateTime, comment="结算开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, comment="结算结束时间")

    # 结算金额
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="总交易金额"
    )
    total_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="总手续费")
    settlement_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), comment="实际结算金额"
    )

    # 交易笔数
    total_count: Mapped[int] = mapped_column(BigInteger, comment="总交易笔数")
    success_count: Mapped[int] = mapped_column(BigInteger, comment="成功交易笔数")
    refund_count: Mapped[int] = mapped_column(BigInteger, comment="退款笔数")

    # 状态
    settlement_status: Mapped[int] = mapped_column(
        SmallInteger, comment="结算状态：0待结算/1已结算/2结算失败"
    )

    # 结算账户信息
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="结算银行"
    )
    bank_account: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="结算账号"
    )

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )
