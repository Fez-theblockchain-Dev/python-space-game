"""
Game Backend API Server
=======================
A simple FastAPI server that other computers can connect to for multiplayer gaming.

Run with: 
    cd backend_apis
    python server.py

Or with auto-reload for development:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================================
# Step 1: Create the FastAPI App
# ============================================================================

app = FastAPI(
    title="Space Game Economy API",
    description="Backend API for multiplayer game connections and wallet management",
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

game_state: dict = {
    "active_games": [],
    "leaderboard": [],
}


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
# Step 8: Run the Server
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
