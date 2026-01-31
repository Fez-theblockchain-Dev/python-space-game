"""
Game Backend API Server
=======================
A simple FastAPI server that other computers can connect to for multiplayer gaming.

Run with: 
    cd backend_apis
    python server.py

Or with auto-reload for development:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

API Endpoints:
==============
Health & Status:
    GET  /                              - Root status check
    GET  /health                        - Health check with player count

Player Management:
    POST /api/player/join               - Register new player
    POST /api/player/leave/{id}         - Remove player from game
    GET  /api/players                   - List all connected players
    POST /api/player/position           - Update player position
    POST /api/player/score              - Update player score

Game State:
    GET  /api/game/state                - Get current game state
    GET  /api/leaderboard               - Get top 10 players

Wallet & Economy:
    GET  /api/wallet/{player_uuid}      - Get player wallet balance
    POST /api/wallet/credit             - Credit player wallet (internal use)
    GET  /api/packages                  - Get available purchase packages

Payment (Stripe):
    POST /api/payments/create-intent    - Create Stripe PaymentIntent
    POST /api/payments/create-checkout  - Create Stripe Checkout session
    POST /api/payments/webhook          - Stripe webhook handler
"""

import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os

# Import payment models and services
try:
    from .models import PackageType, PACKAGES, TransactionStatus
    from .stripe_service import StripePaymentService
    from .stripe_payment_handler import StripePaymentHandler
except ImportError:
    # Handle direct execution vs module import
    from models import PackageType, PACKAGES, TransactionStatus
    from stripe_service import StripePaymentService
    from stripe_payment_handler import StripePaymentHandler


# ============================================================================
# Step 1: Create the FastAPI App
# ============================================================================

app = FastAPI(
    title="Space Game Economy API",
    description="Backend API for browser game connections, wallet management, and Stripe payments",
    version="1.0.0",
)

# ============================================================================
# Step 2: Add CORS Middleware (allows connections from different origins)
# ============================================================================
# This is CRITICAL for allowing other computers/browsers to connect

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# Step 3: In-Memory Data Storage
# ============================================================================
# Simple dictionaries for demo. In production, use a database.

# Global storage for connected players
# Key: player_id (str), Value: dict with player info (name, x, y, score, joined_at)
connected_players: dict[str, dict] = {}

# KPI tracker for user analytics
game_state: dict = {
    "active games": [],
    "leaderboard": [], # Will record who eliminates the most aliens by wallet ID
    "paid users": []
}

# In-memory wallet storage (replace with database in production)
# Key: player_uuid (str), Value: dict with wallet info
player_wallets: dict[str, dict] = {"ID", os.name}

# Initialize Stripe service (uses environment variables)
stripe_service = StripePaymentService()

# Serve the Pygbag game at /play\
GAME_BUILD_PATH = os.path.join(os.path.dirname(__file__), "..", "game", "build", "web")
if os.path.exists(GAME_BUILD_PATH):
    app.mount("/play", StaticFiles(directory=GAME_BUILD_PATH, html=True), name="game")

# ============================================================================
# Step 4: Pydantic Models (Request/Response Validation)
# ============================================================================

class PlayerJoinRequest(BaseModel):
    """Request body when a player joins the game"""
    player_name: str


class PlayerJoinResponse(BaseModel):
    """Response when a player successfully joins"""
    success: bool
    player_id: str
    player_name: str
    message: str


class PlayerPosition(BaseModel):
    """Player position update"""
    player_id: str
    x: float
    y: float


class PlayerScore(BaseModel):
    """Player score update"""
    player_id: str
    score: int


class CreatePaymentIntentRequest(BaseModel):
    """Request to create a Stripe PaymentIntent"""
    player_uuid: str
    package_id: str
    email: Optional[str] = None


class CreateCheckoutRequest(BaseModel):
    """Request to create a Stripe Checkout session"""
    player_uuid: str
    package_id: Optional[str] = None
    items: Optional[list[dict]] = None
    quantity: int = 1
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreditWalletRequest(BaseModel):
    """Request to credit a player's wallet"""
    player_uuid: str
    gold_coins: int = 0
    health_packs: int = 0
    transaction_id: Optional[str] = None


# ============================================================================
# Step 5: API Routes - Health Check
# ============================================================================

@app.get("/")
def root():
    """
    Root endpoint - confirms server is running.
    Test with: curl http://localhost:8000/
    """
    return {
        "status": "online",
        "service": "Space Game Server",
        "version": "1.0.0",
        "message": "Welcome to the Space Game Server! 🚀"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    Test with: curl http://localhost:8000/health
    """
    return {
        "status": "healthy",
        "connected_players": len(connected_players),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Step 6: API Routes - Player Management
# ============================================================================

@app.post("/api/player/join", response_model=PlayerJoinResponse)
def player_join(request: PlayerJoinRequest):
    """
    Register a new player to the game.
    
    Example request body:
    {"player_name": "SpaceHero42"}
    """
    # Generate unique player ID
    player_id = str(uuid.uuid4())[:8]  # Short UUID for simplicity
    
    # Store player data
    connected_players[player_id] = {
        "name": request.player_name,
        "x": 400,  # Starting position
        "y": 300,
        "score": 0,
        "joined_at": datetime.now().isoformat(),
    }
    
    print(f"🎮 Player joined: {request.player_name} (ID: {player_id})")
    
    return PlayerJoinResponse(
        success=True,
        player_id=player_id,
        player_name=request.player_name,
        message=f"Welcome to the game, {request.player_name}!"
    )


@app.post("/api/player/leave/{player_id}")
def player_leave(player_id: str):
    """Remove a player from the game."""
    if player_id not in connected_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player_name = connected_players[player_id]["name"]
    del connected_players[player_id]
    
    print(f"👋 Player left: {player_name} (ID: {player_id})")
    
    return {"success": True, "message": f"Goodbye, {player_name}!"}


@app.get("/api/players")
def get_all_players():
    """Get list of all connected players."""
    return {
        "count": len(connected_players),
        "players": connected_players
    }


# ============================================================================
# Step 7: API Routes - Game State
# ============================================================================

@app.post("/api/player/position")
def update_position(position: PlayerPosition):
    """Update a player's position (called frequently during gameplay)."""
    if position.player_id not in connected_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    connected_players[position.player_id]["x"] = position.x
    connected_players[position.player_id]["y"] = position.y
    
    return {"success": True}


@app.post("/api/player/score")
def update_score(score: PlayerScore):
    """Update a player's score."""
    if score.player_id not in connected_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    connected_players[score.player_id]["score"] = score.score
    
    return {"success": True, "new_score": score.score}


@app.get("/api/game/state")
def get_game_state():
    """Get the current game state (all players and their positions)."""
    return {
        "players": connected_players,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/leaderboard")
def get_leaderboard():
    """Get the top 10 players by score."""
    sorted_players = sorted(
        connected_players.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:10]
    
    return {
        "leaderboard": [
            {"rank": i + 1, "player_id": pid, "name": data["name"], "score": data["score"]}
            for i, (pid, data) in enumerate(sorted_players)
        ]
    }


# ============================================================================
# Step 8: Wallet & Economy Endpoints
# ============================================================================

def get_or_create_wallet(player_uuid: str) -> dict:
    """Get existing wallet or create a new one."""
    if player_uuid not in player_wallets:
        player_wallets[player_uuid] = {
            "player_uuid": player_uuid,
            "gold_coins": 0,
            "health_packs": 0,
            "total_earned_coins": 0,
            "total_earned_health_packs": 0,
            "total_spent_usd": 0.0,
            "created_at": datetime.now().isoformat(),
        }
    return player_wallets[player_uuid]


@app.get("/api/wallet/{player_uuid}")
def get_wallet(player_uuid: str):
    """
    Get player's wallet balance.
    
    Example: GET /api/wallet/abc123
    """
    wallet = get_or_create_wallet(player_uuid)
    return wallet


@app.post("/api/wallet/credit")
def credit_wallet(request: CreditWalletRequest):
    """
    Credit gold coins and/or health packs to a player's wallet.
    
    This endpoint is typically called after a successful payment webhook.
    
    Example request body:
    {
        "player_uuid": "abc123",
        "gold_coins": 100,
        "health_packs": 5,
        "transaction_id": "pi_xxx"
    }
    """
    wallet = get_or_create_wallet(request.player_uuid)
    
    if request.gold_coins > 0:
        wallet["gold_coins"] += request.gold_coins
        wallet["total_earned_coins"] += request.gold_coins
    
    if request.health_packs > 0:
        wallet["health_packs"] += request.health_packs
        wallet["total_earned_health_packs"] += request.health_packs
    
    print(f"💰 Credited {request.gold_coins} gold, {request.health_packs} health to {request.player_uuid}")
    
    return {
        "success": True,
        "wallet": wallet,
        "credited": {
            "gold_coins": request.gold_coins,
            "health_packs": request.health_packs,
        }
    }


@app.get("/api/packages")
def get_packages():
    """
    Get all available packages for purchase.
    
    Returns list of packages with pricing and rewards.
    """
    packages_list = [
        {
            "id": pkg_type.value,
            "name": pkg["name"],
            "price": pkg["price"],
            "gold_coins": pkg["gold_coins"],
            "health_packs": pkg["health_packs"],
        }
        for pkg_type, pkg in PACKAGES.items()
    ]
    return {"packages": packages_list}


# ============================================================================
# Step 9: Stripe Payment Endpoints
# ============================================================================

@app.post("/api/payments/create-intent")
def create_payment_intent(request: CreatePaymentIntentRequest):
    """
    Create a Stripe PaymentIntent for Apple Pay / Express Checkout.
    
    Returns client_secret for use with Stripe.js on the frontend.
    
    Example request body:
    {
        "player_uuid": "abc123",
        "package_id": "gold_100",
        "email": "player@example.com"
    }
    """
    # Validate package
    try:
        package_type = PackageType(request.package_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid package: {request.package_id}")
    
    # Create PaymentIntent via Stripe service
    result = stripe_service.create_payment_intent(
        player_uuid=request.player_uuid,
        package_type=package_type,
        customer_email=request.email,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    # Ensure wallet exists
    get_or_create_wallet(request.player_uuid)
    
    return {
        "success": True,
        "clientSecret": result.client_secret,
        "paymentIntentId": result.payment_intent_id,
        "merchantReference": result.merchant_reference,
        "publishableKey": result.publishable_key,
    }


@app.post("/api/payments/create-checkout")
def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe Checkout Session (hosted payment page).
    
    Supports single package or multiple items.
    
    Example request body (single):
    {
        "player_uuid": "abc123",
        "package_id": "gold_100",
        "quantity": 1
    }
    
    Example request body (multiple):
    {
        "player_uuid": "abc123",
        "items": [
            {"id": "gold_100", "quantity": 2},
            {"id": "health_pack_5", "quantity": 1}
        ]
    }
    """
    # Validate and build items
    if request.items:
        # Multi-item checkout
        for item in request.items:
            try:
                PackageType(item.get("id"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid package: {item.get('id')}")
        package_type = PackageType(request.items[0]["id"])
    elif request.package_id:
        # Single item checkout
        try:
            package_type = PackageType(request.package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid package: {request.package_id}")
    else:
        raise HTTPException(status_code=400, detail="No package specified")
    
    # Create Checkout Session via Stripe service
    result = stripe_service.create_checkout_session(
        player_uuid=request.player_uuid,
        package_type=package_type,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    # Ensure wallet exists
    get_or_create_wallet(request.player_uuid)
    
    return {
        "success": True,
        "sessionId": result.payment_intent_id,  # Note: For checkout, this is actually session ID
        "url": result.checkout_url,
        "merchantReference": result.merchant_reference,
    }


@app.post("/api/payments/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")):
    """
    Handle Stripe webhook events.
    
    Configure this endpoint in Stripe Dashboard:
    Developers > Webhooks > Add endpoint > URL: https://yourdomain.com/api/payments/webhook
    
    Events to listen for:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - checkout.session.completed
    """
    payload = await request.body()
    signature = stripe_signature or ""
    
    # Process webhook through Stripe service
    result = stripe_service.process_webhook(payload, signature)
    
    if not result.valid:
        print(f"⚠️ Invalid webhook: {result.error}")
        raise HTTPException(status_code=400, detail=result.error)
    
    print(f"📨 Received webhook: {result.event_type}")
    
    # Handle successful payments
    if stripe_service.should_credit_player(result.event_type, result.success or False):
        raw_data = result.raw_data or {}
        metadata = raw_data.get("metadata", {})
        
        player_uuid = metadata.get("player_uuid")
        gold_coins = int(metadata.get("gold_coins", 0))
        health_packs = int(metadata.get("health_packs", 0))
        
        if player_uuid:
            # Credit the player's wallet
            wallet = get_or_create_wallet(player_uuid)
            wallet["gold_coins"] += gold_coins
            wallet["health_packs"] += health_packs
            wallet["total_earned_coins"] += gold_coins
            wallet["total_earned_health_packs"] += health_packs
            
            # Calculate amount spent
            package_type_str = metadata.get("package_type")
            if package_type_str:
                try:
                    pkg = PACKAGES.get(PackageType(package_type_str))
                    if pkg:
                        wallet["total_spent_usd"] += pkg["price"]
                except ValueError:
                    pass
            
            print(f"✅ Credited {gold_coins} gold, {health_packs} health to player {player_uuid}")
    
    # Handle failed payments
    if result.event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
        print(f"❌ Payment failed: {result.payment_intent_id}")
    
    return {"received": True, "event_type": result.event_type}


# ============================================================================
# Step 10: Run the Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Starting Space Game Server...")
    print("=" * 60)
    print()
    print("To connect from OTHER computers on your network:")
    print("  1. Find your IP address:")
    print("     - Mac/Linux: ifconfig | grep 'inet '")
    print("     - Windows: ipconfig")
    print("  2. Use that IP, e.g.: http://192.168.1.100:8000")
    print()
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    # host="0.0.0.0" makes the server accessible from other computers
    uvicorn.run(app, host="0.0.0.0", port=8000)
