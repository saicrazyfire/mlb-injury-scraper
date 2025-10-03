"""FastMCP server for MLB injury data."""

import asyncio
import logging
from typing import List, Dict, Any
from fastmcp import FastMCP
from scraper import MLBInjuryScraper, InjuredPlayer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("MLB Injury Scraper")

# Initialize scraper
scraper = MLBInjuryScraper()

@mcp.tool()
def get_team_injuries(team: str) -> List[Dict[str, Any]]:
    """Get current injury report for any MLB team.
    
    Args:
        team: Team key (e.g., 'mets', 'dodgers', 'yankees')
    """
    try:
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        if not injured_players:
            # Check if team exists in config
            available_teams = scraper.get_available_teams()
            if team.lower() not in available_teams:
                return [{
                    "error": f"Team '{team}' not supported. Available teams: {', '.join(available_teams)}"
                }]
            else:
                return [{"message": f"No injury data found for {team}"}]
        
        # Convert to dictionaries for JSON serialization
        result = []
        for player in injured_players:
            result.append({
                "name": player.name,
                "position": player.position,
                "injury": player.injury,
                "il_date": player.il_date,
                "expected_return": player.expected_return,
                "status": player.status,
                "last_updated": player.last_updated
            })
        
        logger.info(f"Retrieved {len(result)} injured players for {team}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting {team} injuries: {e}")
        return [{"error": f"Failed to retrieve injury data for {team}: {str(e)}"}]

@mcp.tool()
def get_mets_injuries() -> List[Dict[str, Any]]:
    """Get current New York Mets injury report with player details (legacy method)."""
    return get_team_injuries('mets')

@mcp.tool()
def get_available_teams() -> Dict[str, Any]:
    """Get list of all available MLB teams that can be queried."""
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
        
        return {
            "total_teams": len(teams),
            "teams": team_info
        }
        
    except Exception as e:
        logger.error(f"Error getting available teams: {e}")
        return {"error": f"Failed to retrieve team list: {str(e)}"}

@mcp.tool()
def get_injury_summary(team: str = 'mets') -> Dict[str, Any]:
    """Get a summary of team injuries including counts by status.
    
    Args:
        team: Team key (e.g., 'mets', 'dodgers', 'yankees'). Defaults to 'mets'.
    """
    try:
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        total_injured = len(injured_players)
        status_counts = {}
        injury_types = {}
        
        for player in injured_players:
            # Count by injury type
            injury_type = player.injury
            injury_types[injury_type] = injury_types.get(injury_type, 0) + 1
        
        return {
            "total_injured_players": total_injured,
            "injury_type_breakdown": injury_types,
            "last_updated": "Real-time data from MLB.com"
        }
        
    except Exception as e:
        logger.error(f"Error getting injury summary for {team}: {e}")
        return {"error": f"Failed to retrieve injury summary for {team}: {str(e)}"}

@mcp.tool()
def search_player_injury(player_name: str, team: str = 'mets') -> Dict[str, Any]:
    """Search for a specific player's injury status.
    
    Args:
        player_name: Name of the player to search for
        team: Team key to search in (e.g., 'mets', 'dodgers', 'yankees'). Defaults to 'mets'.
    """
    try:
        injured_players = scraper.scrape_team_injuries(team.lower())
        
        # Search for player (case-insensitive)
        player_name_lower = player_name.lower()
        for player in injured_players:
            if player_name_lower in player.name.lower():
                return {
                    "found": True,
                    "name": player.name,
                    "position": player.position,
                    "injury": player.injury,
                    "il_date": player.il_date,
                    "expected_return": player.expected_return,
                    "status": player.status,
                    "last_updated": player.last_updated
                }
        
        return {
            "found": False,
            "message": f"No injury information found for player: {player_name} on team: {team}"
        }
        
    except Exception as e:
        logger.error(f"Error searching for player {player_name} on team {team}: {e}")
        return {"error": f"Failed to search for player: {str(e)}"}

def main():
    """Run the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()