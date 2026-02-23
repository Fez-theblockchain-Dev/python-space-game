"""
Database models and shared constants for the payment system.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SqlEnum,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class PackageType(str, Enum):
    STARTER = "gold_100"
    VALUE = "gold_500"
    PREMIUM = "gold_1200"


PACKAGES: dict[PackageType, dict] = {
    PackageType.STARTER: {
        "id": PackageType.STARTER.value,
        "name": "Starter Pack",
        "price": 1.99,
        "gold_coins": 100,
        "health_packs": 1,
    },
    PackageType.VALUE: {
        "id": PackageType.VALUE.value,
        "name": "Value Pack",
        "price": 4.99,
        "gold_coins": 500,
        "health_packs": 6,
    },
    PackageType.PREMIUM: {
        "id": PackageType.PREMIUM.value,
        "name": "Premium Pack",
        "price": 9.99,
        "gold_coins": 1200,
        "health_packs": 15,
    },
}


class TransactionStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELED = "canceled"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    player_uuid = Column[str](String(64), unique=True, nullable=False, index=True)
    created_at = Column[datetime](DateTime, default=lambda: datetime.now(timezone.utc))

    wallet = relationship("PlayerWallet", back_populates="player", uselist=False)
    transactions = relationship("Transaction", back_populates="player")


class PlayerWallet(Base):
    __tablename__ = "player_wallets"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True, nullable=False)
    gold_coins = Column(Integer, default=0, nullable=False)
    health_packs = Column(Integer, default=0, nullable=False)
    total_earned_coins = Column(Integer, default=0, nullable=False)
    total_earned_health_packs = Column(Integer, default=0, nullable=False)
    total_spent_usd = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    player = relationship("Player", back_populates="wallet")

    def add_gold_coins(self, amount: int) -> None:
        if amount <= 0:
            return
        self.gold_coins += amount
        self.total_earned_coins += amount
        self.updated_at = datetime.utcnow()

    def add_health_packs(self, amount: int) -> None:
        if amount <= 0:
            return
        self.health_packs += amount
        self.total_earned_health_packs += amount
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "gold_coins": self.gold_coins,
            "health_packs": self.health_packs,
            "total_earned_coins": self.total_earned_coins,
            "total_earned_health_packs": self.total_earned_health_packs,
            "total_spent_usd": self.total_spent_usd,
        }


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    merchant_reference = Column(String(128), unique=True, nullable=False, index=True)
    psp_reference = Column(String(128), index=True)
    package_type = Column(String(64), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    status = Column(SqlEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    gold_coins_reward = Column(Integer, default=0, nullable=False)
    health_packs_reward = Column(Integer, default=0, nullable=False)
    payment_method = Column(String(64))
    webhook_data = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)

    player = relationship("Player", back_populates="transactions")
