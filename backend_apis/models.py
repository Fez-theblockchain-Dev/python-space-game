"""
Database models for the game economy and payment system.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Float, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TransactionStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PackageType(str, Enum):
    GOLD_100 = "gold_100"
    GOLD_500 = "gold_500"
    GOLD_1000 = "gold_1000"
    HEALTH_PACK_5 = "health_pack_5"
    HEALTH_PACK_10 = "health_pack_10"
    STARTER_BUNDLE = "starter_bundle"


# Package definitions with prices and rewards
PACKAGES = {
    PackageType.GOLD_100: {"price": 0.99, "gold_coins": 100, "health_packs": 0, "name": "100 Gold Coins"},
    PackageType.GOLD_500: {"price": 3.99, "gold_coins": 500, "health_packs": 0, "name": "500 Gold Coins"},
    PackageType.GOLD_1000: {"price": 6.99, "gold_coins": 1000, "health_packs": 0, "name": "1000 Gold Coins"},
    PackageType.HEALTH_PACK_5: {"price": 1.99, "gold_coins": 0, "health_packs": 5, "name": "5 Health Packs"},
    PackageType.HEALTH_PACK_10: {"price": 2.99, "gold_coins": 0, "health_packs": 10, "name": "10 Health Packs"},
    PackageType.STARTER_BUNDLE: {"price": 9.99, "gold_coins": 1500, "health_packs": 20, "name": "Starter Bundle"},
}


class Player(Base):
    """Player account model."""
    __tablename__ = "players"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    wallet: Mapped["PlayerWallet"] = relationship(back_populates="player", uselist=False, cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"Player(id={self.id}, uuid={self.player_uuid})"


class PlayerWallet(Base):
    """Player wallet for storing in-game currency."""
    __tablename__ = "player_wallets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), unique=True)
    gold_coins: Mapped[int] = mapped_column(Integer, default=0)
    health_packs: Mapped[int] = mapped_column(Integer, default=0)
    total_earned_coins: Mapped[int] = mapped_column(Integer, default=0)
    total_earned_health_packs: Mapped[int] = mapped_column(Integer, default=0)
    total_spent_usd: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player: Mapped["Player"] = relationship(back_populates="wallet")
    
    def add_gold_coins(self, amount: int):
        """Add gold coins to wallet."""
        self.gold_coins += amount
        self.total_earned_coins += amount
    
    def add_health_packs(self, amount: int):
        """Add health packs to wallet."""
        self.health_packs += amount
        self.total_earned_health_packs += amount
    
    def spend_gold_coins(self, amount: int) -> bool:
        """Spend gold coins. Returns True if successful."""
        if self.gold_coins >= amount:
            self.gold_coins -= amount
            return True
        return False
    
    def use_health_pack(self) -> bool:
        """Use a health pack. Returns True if successful."""
        if self.health_packs > 0:
            self.health_packs -= 1
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "gold_coins": self.gold_coins,
            "health_packs": self.health_packs,
            "total_earned_coins": self.total_earned_coins,
            "total_earned_health_packs": self.total_earned_health_packs,
            "total_spent_usd": self.total_spent_usd,
        }


class Transaction(Base):
    """Payment transaction record."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    
    # Adyen specific fields
    merchant_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    psp_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Transaction details
    package_type: Mapped[str] = mapped_column(String(50))
    amount_cents: Mapped[int] = mapped_column(Integer)  # Amount in cents
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Rewards to be credited
    gold_coins_reward: Mapped[int] = mapped_column(Integer, default=0)
    health_packs_reward: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    webhook_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of webhook payload
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    player: Mapped["Player"] = relationship(back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, ref={self.merchant_reference}, status={self.status})"

