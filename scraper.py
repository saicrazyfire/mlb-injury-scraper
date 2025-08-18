"""MLB injury data scraper."""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class InjuredPlayer:
    """Represents an injured MLB player."""
    name: str
    position: str
    injury: str
    il_date: Optional[str] = None
    expected_return: Optional[str] = None
    status: Optional[str] = None
    last_updated: Optional[str] = None

class MLBInjuryScraper:
    """Scraper for MLB injury data."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_mets_injuries(self) -> List[InjuredPlayer]:
        """Scrape Mets injury data from MLB.com."""
        url = "https://www.mlb.com/news/mets-injuries-and-roster-moves"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            injured_players = []
            
            # Debug: Print page title to confirm we got the right page
            title = soup.find('title')
            if title:
                logger.info(f"Page title: {title.get_text()}")
            
            # Try multiple selectors for article content
            article_selectors = [
                'div.article-content',
                'article',
                'div.article-wrap',
                'div.article-body',
                'div.content',
                'main',
                'div[class*="article"]',
                'div[class*="content"]'
            ]
            
            article_content = None
            for selector in article_selectors:
                article_content = soup.select_one(selector)
                if article_content:
                    logger.info(f"Found content using selector: {selector}")
                    break
            
            if not article_content:
                # Fallback: look for any div with substantial text content
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().strip()
                    if len(text) > 500 and any(keyword in text.lower() for keyword in ['injury', 'injured', 'il']):
                        article_content = div
                        logger.info("Found content using fallback method")
                        break
            
            if not article_content:
                logger.warning("Could not find article content")
                # Debug: Print some of the page structure
                logger.info("Available div classes:")
                for div in soup.find_all('div', class_=True)[:10]:
                    logger.info(f"  {div.get('class')}")
                return []
            
            # Extract injury information maintaining order
            injury_data = self._extract_structured_injury_info(article_content)
            
            for data in injury_data:
                player = InjuredPlayer(
                    name=data.get('name', 'Unknown'),
                    position=data.get('position', 'Unknown'),
                    injury=data.get('injury', 'Unknown'),
                    il_date=data.get('il_date'),
                    expected_return=data.get('expected_return'),
                    status=data.get('status'),
                    last_updated=data.get('last_updated')
                )
                injured_players.append(player)
            
            return injured_players
            
        except requests.RequestException as e:
            logger.error(f"Error fetching injury data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing injury data: {e}")
            return []
    
    def _extract_structured_injury_info(self, content) -> List[Dict]:
        """Extract injury information from article content, targeting specific div structure."""
        injury_data = []
        
        # Look for the section element within the article
        section = content.find('section')
        if not section:
            logger.warning("Could not find section element")
            # Try looking in the entire article content
            section = content
        
        # Debug: Show what divs are available
        all_divs = section.find_all('div')
        logger.info(f"Found {len(all_divs)} total divs in section")
        
        # Show first few divs with their classes
        for i, div in enumerate(all_divs[:10]):
            div_class = div.get('class', [])
            div_text = div.get_text().strip()[:100]
            logger.info(f"Div {i}: class={div_class}")
            logger.info(f"  Text: {div_text}...")
        
        # Find divs that have both "story-part" AND "markdown" in their class
        markdown_divs = section.find_all('div', class_=lambda x: x and 'story-part' in x and 'markdown' in x)
        logger.info(f"Found {len(markdown_divs)} divs with both story-part and markdown classes")
        
        for i, div in enumerate(markdown_divs):
            div_text = div.get_text().strip()
            
            # Skip empty divs
            if not div_text:
                continue
            
            logger.info(f"Processing div {i}: {div_text[:100]}...")
            
            # Skip header/intro divs that don't contain player data
            if any(skip_phrase in div_text.lower() for skip_phrase in [
                'this page will be updated',
                'latest injuries',
                'get the latest from mlb',
                'sign up to receive',
                'more mets injury news'
            ]):
                logger.info(f"Skipping header/intro div: {div_text[:50]}...")
                continue
            
            # Check if this div starts with a position (indicating a player)
            position_pattern = r'^(C|1B|2B|3B|SS|LF|CF|RF|OF|IF|P|RHP|LHP|DH|INF)\s+'
            if not re.match(position_pattern, div_text):
                logger.info(f"Skipping div - doesn't start with position: {div_text[:50]}...")
                continue
            
            # Parse the player information from this div
            parsed_info = self._parse_player_div(div)
            if parsed_info:
                logger.info(f"Found player: {parsed_info['name']}")
                injury_data.append(parsed_info)
        
        logger.info(f"Total players found: {len(injury_data)}")
        return injury_data
    
    def _parse_player_div(self, div) -> Optional[Dict]:
        """Parse player information from a markdown div element."""
        div_text = div.get_text().strip()
        
        # Extract information from the div text
        player_info = {
            'name': None,
            'position': None,
            'injury': None,
            'il_date': None,
            'expected_return': None,
            'status': None,
            'last_updated': None
        }
        
        # The MLB page has format: "POSITION PlayerNameInjury: ..."
        # Handle names with special characters like ñ, ú, etc.
        mlb_format_match = re.search(r'^([A-Z]{1,3})\s+([A-Z][a-zA-ZñúéíóáüÑÚÉÍÓÁÜ]+(?:\s+[A-Z][a-zA-ZñúéíóáüÑÚÉÍÓÁÜ\'\.]+)+)Injury:\s*(.+?)(?:IL date:|Expected return:|Status:|$)', div_text, re.DOTALL)
        
        if mlb_format_match:
            player_info['position'] = mlb_format_match.group(1)
            player_info['name'] = mlb_format_match.group(2).strip()
            injury_section = mlb_format_match.group(3).strip()
            
            # Clean up injury text
            player_info['injury'] = injury_section
            
            # Extract IL date
            il_match = re.search(r'IL date:\s*([^E]+?)(?:Expected return:|Status:|$)', div_text, re.DOTALL)
            if il_match:
                player_info['il_date'] = il_match.group(1).strip()
            
            # Extract expected return
            return_match = re.search(r'Expected return:\s*([^S]+?)(?:Status:|$)', div_text, re.DOTALL)
            if return_match:
                player_info['expected_return'] = return_match.group(1).strip()
            
            # Extract last updated info first - look for specific "(updated MONTH DAY)" pattern
            # This pattern appears at the end of the text, either at the very end or before "More >>"
            updated_patterns = [
                r'\(updated\s+(\w+\.?\s+\d+)\)',
                r'\(Updated\s+(\w+\.?\s+\d+)\)'
            ]
            
            for pattern in updated_patterns:
                updated_match = re.search(pattern, div_text)
                if updated_match:
                    player_info['last_updated'] = updated_match.group(1)
                    break
            

            
            # Extract status information - get everything after "Status:" but remove the "(updated...)" part
            status_match = re.search(r'Status:\s*(.+)', div_text, re.DOTALL)
            if status_match:
                status_text = status_match.group(1).strip()
                # Remove the "(updated MONTH DAY)" part from status - try multiple patterns
                status_text = re.sub(r'\s*\(updated\s+\w+\.?\s+\d+\)\s*', '', status_text, flags=re.IGNORECASE)
                status_text = re.sub(r'\s*\(Updated\s+\w+\.?\s+\d+\)\s*', '', status_text)
                # Clean up the status text - remove "More >>" if present
                status_text = re.sub(r'\s*More\s*>>\s*', '', status_text)
                status_text = status_text.strip()
                if status_text:
                    player_info['status'] = status_text
            
            return player_info
        
        return None
    
    def _parse_structured_injury_paragraph(self, paragraph, bold_elements) -> Optional[Dict]:
        """Parse injury information from a structured paragraph with bold elements."""
        paragraph_text = paragraph.get_text().strip()
        
        # Extract information from bold text and surrounding context
        player_info = {
            'name': None,
            'position': None,
            'injury': None,
            'il_date': None,
            'expected_return': None,
            'last_updated': None
        }
        
        # The MLB page has a specific format: "POSITION PlayerNameInjury: ..."
        # Let's parse this format specifically
        mlb_format_match = re.search(r'^([A-Z]{1,3})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z\']+)+)Injury:\s*(.+?)(?:IL date:|Expected return:|Status:|$)', paragraph_text, re.DOTALL)
        
        if mlb_format_match:
            player_info['position'] = mlb_format_match.group(1)
            player_info['name'] = mlb_format_match.group(2).strip()
            injury_section = mlb_format_match.group(3).strip()
            
            # Clean up injury text
            player_info['injury'] = injury_section
            
            # Extract IL date
            il_match = re.search(r'IL date:\s*([^E]+?)(?:Expected return:|Status:|$)', paragraph_text, re.DOTALL)
            if il_match:
                player_info['il_date'] = il_match.group(1).strip()
            
            # Extract expected return
            return_match = re.search(r'Expected return:\s*([^S]+?)(?:Status:|$)', paragraph_text, re.DOTALL)
            if return_match:
                player_info['expected_return'] = return_match.group(1).strip()
            
            # Extract status/last updated info
            status_match = re.search(r'Status:\s*(.+)', paragraph_text, re.DOTALL)
            if status_match:
                status_text = status_match.group(1).strip()
                # Look for dates in the status that might indicate last updated
                date_in_status = re.search(r'(\w+\s+\d+)', status_text)
                if date_in_status:
                    player_info['last_updated'] = date_in_status.group(1)
            
            return player_info
        
        # Fallback: try other patterns if the main one doesn't work
        # Look for player name pattern in bold text first
        for bold in bold_elements:
            bold_text = bold.get_text().strip()
            
            # Skip common non-player bold text
            if any(skip_word in bold_text.lower() for skip_word in 
                   ['player name:', 'injury:', 'il date:', 'expected return:', 'status:', 'updated:']):
                continue
            
            # Look for actual player names (First Last format)
            name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z\']+)+)', bold_text)
            if name_match:
                potential_name = name_match.group(1)
                # Validate it's not a common phrase
                if not any(common in potential_name.lower() for common in 
                          ['little league', 'new york', 'major league', 'world series']):
                    player_info['name'] = potential_name
                    break
        
        if not player_info['name']:
            return None
        
        # Extract position - look for patterns like "Player position: C" or "(C)" after name
        position_patterns = [
            r'Player position:\s*([A-Z0-9]+)',
            r'player position:\s*([A-Z0-9]+)',
            r'\(([A-Z0-9]+)\)',  # Position in parentheses
            r'\b(C|1B|2B|3B|SS|LF|CF|RF|OF|IF|P|RHP|LHP|DH)\b'
        ]
        
        for pattern in position_patterns:
            position_match = re.search(pattern, paragraph_text)
            if position_match:
                player_info['position'] = position_match.group(1)
                break
        
        # Extract injury from bold text or context
        injury_patterns = [
            r'Injury:\s*([^\n|]+)',
            r'injury:\s*([^\n|]+)',
            r'((?:right|left)\s+(?:hand|thumb|elbow|shoulder|knee|ankle|back|hamstring|quad|calf|wrist|finger))',
            r'((?:strained|sprained|torn|fractured)\s+[^\n|,]+)',
            r'(hand|thumb|elbow|shoulder|knee|ankle|back|hamstring|quad|calf|wrist|finger)(?:\s+(?:injury|strain|sprain))?'
        ]
        
        for pattern in injury_patterns:
            injury_match = re.search(pattern, paragraph_text, re.IGNORECASE)
            if injury_match:
                if 'injury:' in pattern.lower():
                    player_info['injury'] = injury_match.group(1).strip()
                else:
                    injury_text = injury_match.group(1).strip()
                    # Clean up the injury text
                    injury_text = re.sub(r'\s+', ' ', injury_text)  # Remove extra whitespace
                    player_info['injury'] = injury_text.title()
                break
        
        # Extract IL date
        il_date_patterns = [
            r'IL date:\s*([^|]+)',
            r'il date:\s*([^|]+)',
            r'placed on.*?IL.*?(\w+\s+\d+)',
            r'(\w+\s+\d+).*?IL'
        ]
        
        for pattern in il_date_patterns:
            il_match = re.search(pattern, paragraph_text, re.IGNORECASE)
            if il_match:
                player_info['il_date'] = il_match.group(1).strip()
                break
        
        # Extract expected return
        return_patterns = [
            r'Expected return:\s*([^|]+)',
            r'expected return:\s*([^|]+)',
            r'(day-to-day|day to day)',
            r'expected.*?(\d+\s*(?:days?|weeks?|months?))',
            r'return.*?(\d{4}|season)'
        ]
        
        for pattern in return_patterns:
            return_match = re.search(pattern, paragraph_text, re.IGNORECASE)
            if return_match:
                if 'expected return:' in pattern.lower():
                    player_info['expected_return'] = return_match.group(1).strip()
                else:
                    player_info['expected_return'] = return_match.group(0).strip()
                break
        
        # Extract last updated (look for dates)
        date_patterns = [
            r'Updated:\s*([^|]+)',
            r'updated:\s*([^|]+)',
            r'(\w+\s+\d+,?\s*\d*)'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, paragraph_text, re.IGNORECASE)
            if date_match:
                player_info['last_updated'] = date_match.group(1).strip()
                break
        
        # Only return if we have at least name and some injury info
        if player_info['name'] and (player_info['injury'] or player_info['il_date'] or player_info['expected_return']):
            return player_info
        
        return None