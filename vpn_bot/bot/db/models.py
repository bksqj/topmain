"""SQLAlchemy ORM models: users, subscriptions, payments, referral stats."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # telegram_id of the referrer, if the user joined via a referral deep-link
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    referral_stat: Mapped["ReferralStat | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    plan: Mapped[str] = mapped_column(String(64), nullable=False, default="trial")
    traffic_limit_gb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traffic_used_gb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    marzban_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subscription_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # last node/location tag applied in Marzban (for UI highlighting)
    node_tag: Mapped[str | None] = mapped_column(String(128), nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscription")

    @property
    def is_trial(self) -> bool:
        return self.plan in ("trial", "free")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # external provider payment id (YooKassa invoice id)
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="yookassa")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # plan key the payment is buying, so the webhook knows what to provision
    plan_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="payments")


class ReferralStat(Base):
    __tablename__ = "referral_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    invited_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_paid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    user: Mapped["User"] = relationship(back_populates="referral_stat")
