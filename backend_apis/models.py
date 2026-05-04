"""
Database models and shared constants for the payment system.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
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
    player_uuid = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    wallet = relationship("PlayerWallet", back_populates="player", uselist=False)
    transactions = relationship("Transaction", back_populates="player")


class PlayerWallet(Base):
    """
    Persistent balances for one player. Public identity is ``Player.player_uuid``
    (exposed in API payloads as ``wallet_id`` / ``player_uuid``).
    """

    __tablename__ = "player_wallets"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True, nullable=False)
    gold_coins = Column(Integer, default=0, nullable=False)
    health_packs = Column(Integer, default=0, nullable=False)
    gems = Column(Integer, default=0, nullable=False)
    inventory_keys = Column(Integer, default=0, nullable=False)
    # Client-reported gold not yet folded into ``gold_coins`` (game session buffer).
    session_coins_earned = Column(Integer, default=0, nullable=False)
    total_earned_coins = Column(Integer, default=0, nullable=False)
    total_earned_health_packs = Column(Integer, default=0, nullable=False)
    total_earned_gems = Column(Integer, default=0, nullable=False)
    total_spent_usd = Column(Float, default=0.0, nullable=False)
    total_treasure_chests = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime)
    player = relationship("Player", back_populates="wallet")

    def add_gold_coins(self, amount: int) -> None:
        if amount <= 0:
            return
        self.gold_coins += amount
        self.total_earned_coins += amount
        self.updated_at = datetime.now(timezone.utc)

    def add_health_packs(self, amount: int) -> None:
        if amount <= 0:
            return
        self.health_packs += amount
        self.total_earned_health_packs += amount
        self.updated_at = datetime.now(timezone.utc)

    def add_gems(self, amount: int) -> None:
        if amount <= 0:
            return
        self.gems += amount
        self.total_earned_gems += amount
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        public_id = None
        if self.player is not None:
            public_id = self.player.player_uuid
        base = {
            "gold_coins": self.gold_coins,
            "health_packs": self.health_packs,
            "gems": self.gems,
            "keys": self.inventory_keys,
            "session_coins_earned": self.session_coins_earned,
            "total_earned_coins": self.total_earned_coins,
            "total_earned_health_packs": self.total_earned_health_packs,
            "total_earned_gems": self.total_earned_gems,
            "total_spent_usd": self.total_spent_usd,
            "total_treasure_chests": self.total_treasure_chests,
        }
        if public_id is not None:
            base["player_uuid"] = public_id
            base["wallet_id"] = public_id
        return base


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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime)

    player = relationship("Player", back_populates="transactions")


class PlayerIPRecord(Base):
    """
    Persistent record of the IP addresses new players connect from.

    One row per (player_uuid, ip_address) pair. We upsert on every
    `/api/player/join` call so operators can see:
      - which IPs first introduced a given player UUID,
      - how many times that pairing has been observed,
      - when it was first and last seen.

    IPv6 addresses can be up to 45 characters, so the column is sized 64.
    """

    __tablename__ = "player_ip_records"
    __table_args__ = (
        UniqueConstraint("player_uuid", "ip_address", name="uq_player_ip"),
    )

    id = Column(Integer, primary_key=True)
    player_uuid = Column(String(64), nullable=False, index=True)
    player_name = Column(String(128))
    ip_address = Column(String(64), nullable=False, index=True)
    user_agent = Column(String(512))
    connection_count = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "player_uuid": self.player_uuid,
            "player_name": self.player_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "connection_count": self.connection_count,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }
