"""
Game Backend API Server
=======================
A simple FastAPI server that other computers can connect to for multiplayer gaming.

Run with (from project root):
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
    POST /api/wallet/add-earned-coins   - Add session coins to player wallet
    GET  /api/packages                  - Get available purchase packages

Payment (Stripe):
    POST /api/payments/create-intent    - Create Stripe PaymentIntent
    POST /api/payments/create-checkout  - Create Stripe Checkout session
    POST /api/payments/webhook          - Stripe webhook handler
"""

from starlette.websockets import WebSocket
import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os
import mimetypes

# Register MIME types for pygbag files
mimetypes.add_type("application/zip", ".apk")
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/javascript", ".js")

# Import payment models and services (from backend_apis package)
from backend_apis.models import PackageType, PACKAGES, TransactionStatus
from backend_apis.stripe_service import StripePaymentService
from backend_apis.stripe_payment_handler import StripePaymentHandler

# web socket (WS) implementation imports for persistent connection between pygbag server and client
from fastapi import WebSocket, WebSocketDisconnect
from game.config import GAME_BUILD_PATH, PYGBAG_PORT
import asyncio
import json


# ============================================================================
# Step 1: Create the FastAPI App
# ============================================================================

app = FastAPI(
    title="Space Cowboys Game Economy API",
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

# In-memory wallet storage (replace with database in production)
# Key: player_uuid (str), Value: dict with wallet info
player_wallets: dict[str, dict] = {}

# Initialize Stripe service (uses environment variables)
stripe_service = StripePaymentService()

# ===================================================================================================================
# Step 4: fastAPI web socket connection to help maintain persistent connections between client & server
# ===================================================================================================================

class GameConnectionManager:
    """Tracks active WebSocket connections and provides broadcast helpers."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, player_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[player_id] = websocket
        print(f"🔌 WebSocket connected: {player_id} (total: {len(self.active_connections)})")

    def disconnect(self, player_id: str):
        self.active_connections.pop(player_id, None)
        print(f"🔌 WebSocket disconnected: {player_id} (total: {len(self.active_connections)})")

    async def send_personal(self, player_id: str, data: dict):
        ws = self.active_connections.get(player_id)
        if ws:
            await ws.send_json(data)

    async def broadcast(self, data: dict, exclude: str | None = None):
        for pid, ws in list[tuple[str, WebSocket]](self.active_connections.items()):
            if pid != exclude:
                try:
                    await ws.send_json(data)
                except Exception:
                    self.active_connections.pop(pid, None)

    async def broadcast_game_state(self):
        state = {
            "type": "game_state",
            "players": {
                pid: {"name": p["name"], "x": p["x"], "y": p["y"], "score": p["score"]}
                for pid, p in connected_players.items()
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast(state)


ws_manager = GameConnectionManager()


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    """
    Persistent WebSocket session for a game client served by Pygbag (port 8666).

    Connect from the browser:
        const ws = new WebSocket("ws://localhost:8000/ws/<player_id>");

    Message protocol (JSON):
        -> { "type": "position", "x": 100, "y": 200 }
        -> { "type": "score",    "score": 42 }
        -> { "type": "chat",     "message": "hello" }
        -> { "type": "ping" }
        <- { "type": "pong" }
        <- { "type": "game_state", "players": { ... } }
    """
    await ws_manager.connect(player_id, websocket)

    if player_id not in connected_players:
        connected_players[player_id] = {
            "name": f"Player_{player_id[:4]}",
            "x": 400,
            "y": 300,
            "score": 0,
            "joined_at": datetime.now().isoformat(),
        }

    await ws_manager.send_personal(player_id, {
        "type": "welcome",
        "player_id": player_id,
        "players": connected_players,
        "pygbag_port": PYGBAG_PORT,
    })

    await ws_manager.broadcast({
        "type": "player_joined",
        "player_id": player_id,
        "name": connected_players[player_id]["name"],
    }, exclude=player_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "position":
                if player_id in connected_players:
                    connected_players[player_id]["x"] = data.get("x", 0)
                    connected_players[player_id]["y"] = data.get("y", 0)
                await ws_manager.broadcast({
                    "type": "player_moved",
                    "player_id": player_id,
                    "x": data.get("x", 0),
                    "y": data.get("y", 0),
                }, exclude=player_id)

            elif msg_type == "score":
                if player_id in connected_players:
                    connected_players[player_id]["score"] = data.get("score", 0)
                await ws_manager.broadcast({
                    "type": "score_update",
                    "player_id": player_id,
                    "score": data.get("score", 0),
                })

            elif msg_type == "chat":
                await ws_manager.broadcast({
                    "type": "chat",
                    "player_id": player_id,
                    "message": data.get("message", ""),
                })

            elif msg_type == "game_state_request":
                await ws_manager.broadcast_game_state()

            elif msg_type == "ping":
                await ws_manager.send_personal(player_id, {"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(player_id)
        if player_id in connected_players:
            del connected_players[player_id]
        await ws_manager.broadcast({
            "type": "player_left",
            "player_id": player_id,
        })



# Serve the Pygbag game at /play
# Note: pygbag builds require specific MIME types for .apk files (zip archives)
print(f"📁 Game build path: {GAME_BUILD_PATH}")
print(f"📁 Game build exists: {os.path.exists(GAME_BUILD_PATH)}")

if os.path.exists(GAME_BUILD_PATH):
    # List files in the build directory for debugging
    try:
        files = os.listdir(GAME_BUILD_PATH)
        print(f"📁 Game build files: {files}")
    except Exception as e:
        print(f"⚠️ Could not list game build files: {e}")
        print(GAME_BUILD_PATH)
    
    app.mount("/play", StaticFiles(directory=GAME_BUILD_PATH, html=True), name="game")
    print("✅ Mounted pygbag game at /play")
else:
    print(f"⚠️ Game build not found at {GAME_BUILD_PATH}")

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


class AddEarnedCoinsRequest(BaseModel):
    """Request to add coins earned from gameplay to a player's wallet"""
    player_uuid: str
    amount: int


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
        "service": "Space Cowboys Game Server",
        "version": "1.0.0",
        "message": "Welcome to the Space Cowboys Game Server! 🚀"
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


@app.get("/play/game.apk")
async def serve_game_apk():
    """
    Serve the pygbag game APK with correct MIME type and CORS headers.
    The .apk file is actually a ZIP archive containing the game assets.
    """
    apk_path = os.path.join(GAME_BUILD_PATH, "game.apk")
    if not os.path.exists(apk_path):
        raise HTTPException(status_code=404, detail="Game APK not found")
    
    return FileResponse(
        apk_path,
        media_type="application/zip",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        }
    )


@app.get("/game-status")
def game_status():
    """
    Check if the pygbag game build is available.
    Test with: curl http://localhost:8000/game-status
    """
    game_available = os.path.exists(GAME_BUILD_PATH)
    files = []
    
    if game_available:
        try:
            files = os.listdir(GAME_BUILD_PATH)
        except Exception:
            pass
    
    return {
        "game_available": game_available,
        "game_path": GAME_BUILD_PATH,
        "game_url": "/play" if game_available else None,
        "files": files,
        "instructions": "Access the game at http://localhost:8000/play" if game_available else "Run 'pygbag game/main.py' to build the game first"
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


@app.post("/api/wallet/add-earned-coins")
def add_earned_coins(request: AddEarnedCoinsRequest):
    """
    Add coins earned from a Space Cowboys🚀 session to the player's wallet.
    
    Called by the game client when a session ends (e.g., level complete, game over).
    Updates the player's wallet in player_wallets by their UUID.
    
    Example request body:
    {
        "player_uuid": "abc-123-def-456",
        "amount": 150
    }
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    wallet = get_or_create_wallet(request.player_uuid)
    wallet["gold_coins"] += request.amount
    wallet["total_earned_coins"] += request.amount
    
    new_balance = wallet["gold_coins"]
    print(f"💰 Session coins: +{request.amount} for {request.player_uuid} (balance: {new_balance})")
    
    return {
        "success": True,
        "coins_added": request.amount,
        "new_balance": new_balance,
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
    print("🚀 Starting Space Cowboys Game Server...")
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
