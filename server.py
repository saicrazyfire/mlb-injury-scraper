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
def get_mets_injuries() -> List[Dict[str, Any]]:
    """Get current New York Mets injury report with player details."""
    try:
        injured_players = scraper.scrape_mets_injuries()
        
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
        
        logger.info(f"Retrieved {len(result)} injured players")
        return result
        
    except Exception as e:
        logger.error(f"Error getting Mets injuries: {e}")
        return [{"error": f"Failed to retrieve injury data: {str(e)}"}]

@mcp.tool()
def get_injury_summary() -> Dict[str, Any]:
    """Get a summary of Mets injuries including counts by status."""
    try:
        injured_players = scraper.scrape_mets_injuries()
        
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
        logger.error(f"Error getting injury summary: {e}")
        return {"error": f"Failed to retrieve injury summary: {str(e)}"}

@mcp.tool()
def search_player_injury(player_name: str) -> Dict[str, Any]:
    """Search for a specific player's injury status."""
    try:
        injured_players = scraper.scrape_mets_injuries()
        
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
            "message": f"No injury information found for player: {player_name}"
        }
        
    except Exception as e:
        logger.error(f"Error searching for player {player_name}: {e}")
        return {"error": f"Failed to search for player: {str(e)}"}

def main():
    """Run the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()