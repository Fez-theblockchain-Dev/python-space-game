"""
Game Backend API Server

Handles:
- Player wallet management
- Stripe payment integration (checkout sessions, webhooks)
- Transaction history
"""
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# from .models import Base, PackageType, PACKAGES
# from .payment_handler import PaymentHandler


# ============================================================================
# Configuration
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game_economy.db")

# ============================================================================
# Database Setup
# ============================================================================

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Service Setup
# ============================================================================


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed

app = FastAPI(
    title="Space Game Economy API",
    description="Backend API for in-game purchases and wallet management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for game client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class CreateSessionRequest(BaseModel):
    player_uuid: str
    package_id: str  # e.g., "gold_100", "health_pack_5"
    use_payment_link: bool = False
    email: Optional[str] = None


class CreateSessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    session_data: Optional[str] = None
    checkout_url: Optional[str] = None
    merchant_reference: Optional[str] = None
    error: Optional[str] = None


class WalletResponse(BaseModel):
    gold_coins: int
    health_packs: int
    total_earned_coins: int
    total_earned_health_packs: int
    total_spent_usd: float


class PackageResponse(BaseModel):
    id: str
    name: str
    price_usd: float
    gold_coins: int
    health_packs: int


class TransactionResponse(BaseModel):
    reference: str
    package: str
    amount_usd: float
    status: str
    gold_coins: int
    health_packs: int
    created_at: str
    completed_at: Optional[str] = None


class SpendCoinsRequest(BaseModel):
    player_uuid: str
    amount: int


class UseHealthPackRequest(BaseModel):
    player_uuid: str


class AddEarnedCoinsRequest(BaseModel):
    player_uuid: str
    amount: int


# ============================================================================
# API Routes - Health Check
# ============================================================================

@app.get("/")
def root():
    return {"status": "ok", "service": "Space Game Economy API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ============================================================================
# API Routes - Packages
# ============================================================================

@app.get("/api/packages", response_model=list[PackageResponse])
def get_packages():
    """Get all available purchase packages."""
    return payment_handler.get_available_packages()


# ============================================================================
# API Routes - Wallet
# ============================================================================

@app.get("/api/wallet/{player_uuid}", response_model=WalletResponse)
def get_wallet(player_uuid: str, db: Session = Depends(get_db)):
    """Get player's wallet balance."""
    # Ensure player exists
    payment_handler.get_or_create_player(db, player_uuid)
    
    wallet = payment_handler.get_player_wallet(db, player_uuid)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(**wallet)


@app.post("/api/wallet/spend")
def spend_coins(request: SpendCoinsRequest, db: Session = Depends(get_db)):
    """Spend gold coins from wallet."""
    from .models import Player
    
    player = db.query(Player).filter(Player.player_uuid == request.player_uuid).first()
    
    if not player or not player.wallet:
        raise HTTPException(status_code=404, detail="Player or wallet not found")
    
    if not player.wallet.spend_gold_coins(request.amount):
        raise HTTPException(status_code=400, detail="Insufficient gold coins")
    
    db.commit()
    
    return {
        "success": True,
        "new_balance": player.wallet.gold_coins,
    }


@app.post("/api/wallet/use-health-pack")
def use_health_pack(request: UseHealthPackRequest, db: Session = Depends(get_db)):
    """Use a health pack from wallet."""
    from .models import Player
    
    player = db.query(Player).filter(Player.player_uuid == request.player_uuid).first()
    
    if not player or not player.wallet:
        raise HTTPException(status_code=404, detail="Player or wallet not found")
    
    if not player.wallet.use_health_pack():
        raise HTTPException(status_code=400, detail="No health packs available")
    
    db.commit()
    
    return {
        "success": True,
        "health_packs_remaining": player.wallet.health_packs,
    }


@app.post("/api/wallet/add-earned-coins")
def add_earned_coins(request: AddEarnedCoinsRequest, db: Session = Depends(get_db)):
    """
    Add coins earned from gameplay to player's wallet.
    
    Called at the end of a level/session to save earned coins.
    """
    from .models import Player
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    player = payment_handler.get_or_create_player(db, request.player_uuid)
    
    if not player.wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    player.wallet.add_gold_coins(request.amount)
    db.commit()
    
    return {
        "success": True,
        "coins_added": request.amount,
        "new_balance": player.wallet.gold_coins,
    }


# ============================================================================
# API Routes - Payments
# ============================================================================

@app.post("/api/payment/create-session", response_model=CreateSessionResponse)
def create_payment_session(request: CreateSessionRequest, db: Session = Depends(get_db)):
    """
    Create a Stripe checkout session for a package purchase.
    
    Returns session data or a checkout URL for redirect.
    """
    # Validate package
    try:
        package_type = PackageType(request.package_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid package_id. Available: {[p.value for p in PackageType]}"
        )
    
    result = payment_handler.initiate_purchase(
        db=db,
        player_uuid=request.player_uuid,
        package_type=package_type,
        use_payment_link=request.use_payment_link,
        shopper_email=request.email,
    )
    
    return CreateSessionResponse(
        success=result.success,
        session_id=result.session_id,
        session_data=result.session_data,
        checkout_url=result.checkout_url,
        merchant_reference=result.merchant_reference,
        error=result.error,
    )


@app.get("/api/payment/result")
def payment_result(ref: str, redirectResult: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Handle redirect after payment completion.
    
    This endpoint is called when the user returns from the Stripe checkout page.
    The actual crediting happens via webhooks, but this confirms the transaction status.
    """
    result = payment_handler.verify_and_credit_redirect(
        db=db,
        merchant_reference=ref,
        redirect_result=redirectResult,
    )
    
    if result.success and result.new_balance:
        return {
            "status": "success",
            "message": "Payment completed!",
            "gold_coins_added": result.gold_coins_added,
            "health_packs_added": result.health_packs_added,
            "new_balance": result.new_balance,
        }
    elif result.success:
        return {
            "status": "pending",
            "message": result.error or "Payment is being processed",
        }
    else:
        return {
            "status": "failed",
            "message": result.error or "Payment could not be verified",
        }


@app.post("/api/payment/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook notifications.
    
    This is called by Stripe when payment events occur (payment_intent.succeeded, etc.).
    """
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=400)
    
    success, message = payment_handler.process_webhook_notification(db, payload)
    
    if not success:
        print(f"Webhook processing warning: {message}")
    
    return Response(status_code=200)


@app.get("/api/payment/transactions/{player_uuid}", response_model=list[TransactionResponse])
def get_transactions(player_uuid: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get transaction history for a player."""
    transactions = payment_handler.get_transaction_history(db, player_uuid, limit)
    return [TransactionResponse(**t) for t in transactions]


# ============================================================================
# API Routes - Admin/Debug (remove or protect in production)
# ============================================================================

@app.post("/api/admin/credit-test")
def admin_credit_test(player_uuid: str, gold_coins: int = 0, health_packs: int = 0, db: Session = Depends(get_db)):
    """
    Admin endpoint to manually credit a player (for testing).
    REMOVE OR PROTECT THIS IN PRODUCTION!
    """
    from .models import Player
    
    player = payment_handler.get_or_create_player(db, player_uuid)
    
    if gold_coins > 0:
        player.wallet.add_gold_coins(gold_coins)
    if health_packs > 0:
        player.wallet.add_health_packs(health_packs)
    
    db.commit()
    
    return {
        "success": True,
        "wallet": player.wallet.to_dict(),
    }
