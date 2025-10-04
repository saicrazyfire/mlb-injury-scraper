"""HTTP/REST API server for MLB injury data with SSE support."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from sse_starlette.sse import EventSourceResponse

from scraper import MLBInjuryScraper, InjuredPlayer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scraper instance
scraper: Optional[MLBInjuryScraper] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the scraper."""
    global scraper
    scraper = MLBInjuryScraper()
    logger.info("MLB Injury Scraper HTTP server started")
    yield
    logger.info("MLB Injury Scraper HTTP server shutting down")

# Create FastAPI app
app = FastAPI(
    title="MLB Injury Scraper API",
    description="REST API for MLB injury data with real-time updates",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class InjuredPlayerResponse(BaseModel):
    name: str
    position: str
    injury: str
    il_date: Optional[str] = None
    expected_return: Optional[str] = None
    status: Optional[str] = None
    last_updated: Optional[str] = None

class TeamInjuriesResponse(BaseModel):
    team: str
    team_name: str
    total_injured: int
    players: List[InjuredPlayerResponse]

class InjurySummaryResponse(BaseModel):
    team: str
    total_injured_players: int
    injury_type_breakdown: Dict[str, int]
    last_updated: str

class AvailableTeamsResponse(BaseModel):
    total_teams: int
    teams: Dict[str, Dict[str, str]]

class PlayerSearchResponse(BaseModel):
    found: bool
    player: Optional[InjuredPlayerResponse] = None
    message: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mlb-injury-scraper"}

# Get available teams
@app.get("/api/teams", response_model=AvailableTeamsResponse)
async def get_available_teams():
    """Get list of all available MLB teams."""
    try:
        teams = scraper.get_available_teams()
        team_info = {}
        
        for team_key in teams:
            info = scraper.get_team_info(team_key)
            if info:
                team_info[team_key] = {
                    "name": info.get('name', team_key),
                    "abbreviation": info.get('abbreviation', team_key.upper())
                }
        
        return AvailableTeamsResponse(
            total_teams=len(teams),
            teams=team_info
        )
        
    except Exception as e:
        logger.error(f"Error getting available teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve team list: {str(e)}")

# Get team injuries
@app.get("/api/teams/{team}/injuries", response_model=TeamInjuriesResponse)
async def get_team_injuries(team: str):
    """Get current injury report for a specific MLB team."""
    try:
        # Validate team exists
        available_teams = scraper.get_available_teams()
        if team.lower() not in available_teams:
            raise HTTPException(
                status_code=404, 
                detail=f"Team '{team}' not supported. Available teams: {', '.join(available_teams)}"
            )
        
        team_info = scraper.get_team_info(team.lower())
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        players = [
            InjuredPlayerResponse(
                name=player.name,
                position=player.position,
                injury=player.injury,
                il_date=player.il_date,
                expected_return=player.expected_return,
                status=player.status,
                last_updated=player.last_updated
            )
            for player in injured_players
        ]
        
        return TeamInjuriesResponse(
            team=team.lower(),
            team_name=team_info.get('name', team) if team_info else team,
            total_injured=len(players),
            players=players
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {team} injuries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve injury data for {team}: {str(e)}")

# Get injury summary
@app.get("/api/teams/{team}/summary", response_model=InjurySummaryResponse)
async def get_injury_summary(team: str):
    """Get injury summary for a specific team."""
    try:
        # Validate team exists
        available_teams = scraper.get_available_teams()
        if team.lower() not in available_teams:
            raise HTTPException(
                status_code=404, 
                detail=f"Team '{team}' not supported. Available teams: {', '.join(available_teams)}"
            )
        
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        total_injured = len(injured_players)
        injury_types = {}
        
        for player in injured_players:
            injury_type = player.injury
            injury_types[injury_type] = injury_types.get(injury_type, 0) + 1
        
        return InjurySummaryResponse(
            team=team.lower(),
            total_injured_players=total_injured,
            injury_type_breakdown=injury_types,
            last_updated="Real-time data from MLB.com"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting injury summary for {team}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve injury summary for {team}: {str(e)}")

# Search for player
@app.get("/api/teams/{team}/players/{player_name}", response_model=PlayerSearchResponse)
async def search_player_injury(team: str, player_name: str):
    """Search for a specific player's injury status on a team."""
    try:
        # Validate team exists
        available_teams = scraper.get_available_teams()
        if team.lower() not in available_teams:
            raise HTTPException(
                status_code=404, 
                detail=f"Team '{team}' not supported. Available teams: {', '.join(available_teams)}"
            )
        
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        # Search for player (case-insensitive)
        player_name_lower = player_name.lower()
        for player in injured_players:
            if player_name_lower in player.name.lower():
                return PlayerSearchResponse(
                    found=True,
                    player=InjuredPlayerResponse(
                        name=player.name,
                        position=player.position,
                        injury=player.injury,
                        il_date=player.il_date,
                        expected_return=player.expected_return,
                        status=player.status,
                        last_updated=player.last_updated
                    )
                )
        
        return PlayerSearchResponse(
            found=False,
            message=f"No injury information found for player: {player_name} on team: {team}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching for player {player_name} on team {team}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search for player: {str(e)}")

# SSE endpoint for real-time updates
@app.get("/api/teams/{team}/injuries/stream")
async def stream_team_injuries(team: str, interval: int = Query(30, ge=10, le=300)):
    """Stream real-time injury updates for a team via Server-Sent Events."""
    
    async def generate_injury_updates():
        """Generate injury updates at specified intervals."""
        while True:
            try:
                # Validate team exists
                available_teams = scraper.get_available_teams()
                if team.lower() not in available_teams:
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "error": f"Team '{team}' not supported. Available teams: {', '.join(available_teams)}"
                        })
                    }
                    break
                
                team_info = scraper.get_team_info(team.lower())
                injured_players = scraper.scrape_team_injuries(team.lower())
                
                players_data = [
                    {
                        "name": player.name,
                        "position": player.position,
                        "injury": player.injury,
                        "il_date": player.il_date,
                        "expected_return": player.expected_return,
                        "status": player.status,
                        "last_updated": player.last_updated
                    }
                    for player in injured_players
                ]
                
                update_data = {
                    "team": team.lower(),
                    "team_name": team_info.get('name', team) if team_info else team,
                    "total_injured": len(players_data),
                    "players": players_data,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                yield {
                    "event": "injury_update",
                    "data": json.dumps(update_data)
                }
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in SSE stream for {team}: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
                await asyncio.sleep(interval)
    
    return EventSourceResponse(generate_injury_updates())

# Legacy endpoints for backward compatibility
@app.get("/api/mets/injuries")
async def get_mets_injuries():
    """Legacy endpoint for Mets injuries (redirects to new API)."""
    return await get_team_injuries("mets")

# Root endpoint with API documentation
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "MLB Injury Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "teams": "/api/teams",
            "team_injuries": "/api/teams/{team}/injuries",
            "injury_summary": "/api/teams/{team}/summary",
            "player_search": "/api/teams/{team}/players/{player_name}",
            "sse_stream": "/api/teams/{team}/injuries/stream?interval={seconds}",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "example_teams": ["mets", "dodgers", "yankees", "astros", "braves"]
    }

def run_http_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the HTTP server."""
    logger.info(f"Starting MLB Injury Scraper HTTP server on {host}:{port}")
    uvicorn.run(
        "http_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_http_server()
