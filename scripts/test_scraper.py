"""Test script for the MLB injury scraper."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import MLBInjuryScraper

def main():
    """Test the scraper functionality."""
    print("Testing MLB Injury Scraper...")
    
    # Enable logging to see debug info
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    scraper = MLBInjuryScraper()
    
    # Test available teams
    print("\n=== Available Teams ===")
    teams = scraper.get_available_teams()
    print(f"Found {len(teams)} teams in configuration:")
    for team_key in teams[:5]:  # Show first 5 teams
        team_info = scraper.get_team_info(team_key)
        if team_info:
            print(f"  {team_key}: {team_info['name']} ({team_info['abbreviation']})")
    if len(teams) > 5:
        print(f"  ... and {len(teams) - 5} more teams")
    
    # Test teams to scrape
    test_teams = ['mets', 'dodgers', 'yankees']
    
    for team in test_teams:
        print(f"\n=== Testing {team.upper()} ===")
        try:
            injured_players = scraper.scrape_team_injuries(team)
            
            print(f"Found {len(injured_players)} injured players:")
            print("-" * 50)
            
            for player in injured_players[:3]:  # Show first 3 players max
                print(f"Player name: {player.name}")
                print(f"Player position: {player.position}")
                print(f"Injury: {player.injury}")
                if player.il_date:
                    print(f"IL date: {player.il_date}")
                if player.expected_return:
                    print(f"Expected return: {player.expected_return}")
                if player.status:
                    print(f"Status: {player.status}")
                if player.last_updated:
                    print(f"Last updated: {player.last_updated}")
                print()  # Add blank line between players
                print("-" * 50)
            
            if len(injured_players) > 3:
                print(f"... and {len(injured_players) - 3} more injured players")
            
            if not injured_players:
                print("No injury data found. This could mean:")
                print("1. No players are currently injured")
                print("2. The website structure has changed")
                print("3. The page couldn't be accessed")
                
        except Exception as e:
            print(f"Error testing {team} scraper: {e}")
            import traceback
            traceback.print_exc()
    
    # Test legacy method
    print(f"\n=== Testing Legacy Mets Method ===")
    try:
        injured_players = scraper.scrape_mets_injuries()
        print(f"Legacy method found {len(injured_players)} injured Mets players")
    except Exception as e:
        print(f"Error testing legacy method: {e}")

if __name__ == "__main__":
    main()