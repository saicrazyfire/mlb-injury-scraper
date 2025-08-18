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
    
    try:
        injured_players = scraper.scrape_mets_injuries()
        
        print(f"\nFound {len(injured_players)} injured players:")
        print("-" * 50)
        
        for player in injured_players:
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
        
        if not injured_players:
            print("No injury data found. This could mean:")
            print("1. No players are currently injured")
            print("2. The website structure has changed")
            print("3. The page couldn't be accessed")
            print("\nTrying to fetch the page directly to check...")
            
            # Debug: Try to fetch and show some page content
            import requests
            try:
                response = requests.get("https://www.mlb.com/news/mets-injuries-and-roster-moves", timeout=10)
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    title = soup.find('title')
                    if title:
                        print(f"Page title: {title.get_text()}")
                    
                    # Show first few paragraphs
                    paragraphs = soup.find_all('p')[:5]
                    print(f"\nFirst few paragraphs ({len(paragraphs)}):")
                    for i, p in enumerate(paragraphs):
                        text = p.get_text().strip()
                        if text:
                            print(f"{i+1}: {text[:200]}...")
            except Exception as debug_e:
                print(f"Debug fetch failed: {debug_e}")
            
    except Exception as e:
        print(f"Error testing scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()