"""Example HTTP client for the MLB Injury Scraper API."""

import asyncio
import json
import requests
from typing import Dict, Any, List
import httpx

class MLBInjuryAPIClient:
    """Client for the MLB Injury Scraper HTTP API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_available_teams(self) -> Dict[str, Any]:
        """Get all available teams."""
        response = self.session.get(f"{self.base_url}/api/teams")
        response.raise_for_status()
        return response.json()
    
    def get_team_injuries(self, team: str) -> Dict[str, Any]:
        """Get injuries for a specific team."""
        response = self.session.get(f"{self.base_url}/api/teams/{team}/injuries")
        response.raise_for_status()
        return response.json()
    
    def get_injury_summary(self, team: str) -> Dict[str, Any]:
        """Get injury summary for a team."""
        response = self.session.get(f"{self.base_url}/api/teams/{team}/summary")
        response.raise_for_status()
        return response.json()
    
    def search_player(self, team: str, player_name: str) -> Dict[str, Any]:
        """Search for a player on a team."""
        response = self.session.get(f"{self.base_url}/api/teams/{team}/players/{player_name}")
        response.raise_for_status()
        return response.json()
    
    async def stream_team_injuries(self, team: str, interval: int = 30):
        """Stream real-time injury updates via SSE."""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/teams/{team}/injuries/stream?interval={interval}"
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue

def main():
    """Example usage of the MLB Injury API client."""
    client = MLBInjuryAPIClient()
    
    print("🏥 MLB Injury Scraper API Client Example")
    print("=" * 50)
    
    try:
        # Health check
        print("\n1. Health Check:")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        
        # Get available teams
        print("\n2. Available Teams:")
        teams_data = client.get_available_teams()
        print(f"   Total teams: {teams_data['total_teams']}")
        print("   Sample teams:")
        for team_key, team_info in list(teams_data['teams'].items())[:5]:
            print(f"     - {team_key}: {team_info['name']} ({team_info['abbreviation']})")
        
        # Test with specific teams
        test_teams = ['mets', 'dodgers', 'yankees']
        
        for team in test_teams:
            print(f"\n3. {team.upper()} Injuries:")
            try:
                injuries = client.get_team_injuries(team)
                print(f"   Team: {injuries['team_name']}")
                print(f"   Total injured: {injuries['total_injured']}")
                
                if injuries['players']:
                    print("   Recent injuries:")
                    for player in injuries['players'][:3]:  # Show first 3
                        print(f"     - {player['name']} ({player['position']}): {player['injury']}")
                
                # Get summary
                summary = client.get_injury_summary(team)
                print(f"   Injury types: {len(summary['injury_type_breakdown'])}")
                
            except requests.exceptions.HTTPError as e:
                print(f"   Error: {e}")
        
        # Search for a player
        print("\n4. Player Search Example:")
        try:
            search_result = client.search_player('mets', 'Pete')
            if search_result['found']:
                player = search_result['player']
                print(f"   Found: {player['name']} - {player['injury']}")
            else:
                print(f"   {search_result['message']}")
        except requests.exceptions.HTTPError as e:
            print(f"   Search error: {e}")
        
        print("\n5. SSE Stream Example:")
        print("   To test real-time streaming, run:")
        print("   python -c \"import asyncio; from examples.http_client_example import stream_example; asyncio.run(stream_example())\"")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running with: python server.py --http")
    except Exception as e:
        print(f"❌ Error: {e}")

async def stream_example():
    """Example of streaming real-time updates."""
    client = MLBInjuryAPIClient()
    
    print("🔄 Streaming Mets injuries (press Ctrl+C to stop)...")
    try:
        count = 0
        async for update in client.stream_team_injuries('mets', interval=10):
            count += 1
            print(f"\n📡 Update #{count}:")
            print(f"   Team: {update['team_name']}")
            print(f"   Total injured: {update['total_injured']}")
            print(f"   Timestamp: {update['timestamp']}")
            
            if count >= 3:  # Stop after 3 updates for demo
                print("\n✅ Demo complete!")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Streaming stopped by user")
    except Exception as e:
        print(f"❌ Streaming error: {e}")

if __name__ == "__main__":
    main()