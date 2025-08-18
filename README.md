# MLB Injury Scraper with MCP Server

A Python application that scrapes MLB injury data from MLB.com and serves it via FastMCP for integration with AI tools.

## Source & Parsing Logic

**Website URL**: https://www.mlb.com/news/mets-injuries-and-roster-moves

### HTML Structure Analysis
The scraper targets the specific HTML structure of the MLB injury page:
- **Container**: `<article>` element containing a `<section>` sub-element
- **Target Divs**: Divs with classes `story-part` AND `markdown` 
- **Content Format**: Each injury entry follows the pattern: `POSITION PlayerNameInjury: [details]IL date: [date]Expected return: [timeline]Status: [description](updated MONTH DAY)`

### Parsing Strategy
1. **Content Selection**: Finds divs with both `story-part` and `markdown` classes
2. **Header Filtering**: Skips non-player content (intro text, "Latest Injuries" headers)
3. **Player Validation**: Only processes divs starting with valid position codes (C, RHP, LHP, etc.)
4. **Data Extraction**: Uses regex patterns to extract structured data from each player's text block
5. **Order Preservation**: Maintains original order (most recent injuries first)

### Data Fields Extracted
- **Player Name**: Extracted from position + name pattern
- **Position**: Baseball position abbreviations (C, 1B, RHP, etc.)
- **Injury**: Specific injury description
- **IL Date**: Injured List placement date with details
- **Expected Return**: Recovery timeline
- **Status**: Detailed injury status and recovery progress
- **Last Updated**: Date from "(updated MONTH DAY)" pattern

## Features

- Scrapes New York Mets injury data from MLB.com in real-time
- Handles special characters in player names (e.g., Dedniel Núñez)
- Maintains chronological order (most recent injuries first)
- Serves data via FastMCP server for AI tool integration
- Provides multiple tools for different data views
- Robust error handling and logging

## Installation

1. Install using uv:
```bash
uv sync
```

## Usage

### Testing the Scraper
```bash
uv run python scripts/test_scraper.py
```

### Running the MCP Server
```bash
uv run mlb-injury-server
```

### MCP Tools Available

1. **get_mets_injuries()** - Get complete injury report with all fields
2. **get_injury_summary()** - Get summary with counts and breakdowns  
3. **search_player_injury(player_name)** - Search for specific player

## MCP Configuration

Add to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

**Option 1: Using virtual environment Python directly (recommended)**
```json
{
  "mcpServers": {
    "mlb-injury-scraper": {
      "command": "/path/to/your/project/.venv/Scripts/python.exe",
      "args": ["/path/to/your/project/server.py"]
    }
  }
}
```

**Option 2: Using uvx (after installing the package)**
First install the package:
```bash
uv sync
uv pip install -e .
```

Then use this configuration:
```json
{
  "mcpServers": {
    "mlb-injury-scraper": {
      "command": "uvx",
      "args": ["--from", "/path/to/your/project", "mlb-injury-server"]
    }
  }
}
```

**Important**: Replace `/path/to/your/project` with the absolute path to your project directory. Use forward slashes `/` in JSON even on Windows (e.g., `C:/Users/username/project`).

## Data Structure

Each injured player includes:
- **Name**: Player's full name
- **Position**: Baseball position (C, RHP, LHP, 1B, etc.)
- **Injury**: Specific injury description (e.g., "Right thumb", "Sprained UCL in right elbow")
- **IL Date**: Injured List date with details (e.g., "March 27 (60-day IL)")
- **Expected Return**: Recovery timeline (e.g., "Day to day", "2026", "Mid-to-late August")
- **Status**: Detailed injury status and recovery progress
- **Last Updated**: Most recent update date (e.g., "Aug. 17", "March 12")

## Technical Details

- **Language**: Python 3.12+
- **Dependencies**: requests, beautifulsoup4, fastmcp, pydantic, lxml
- **Web Scraping**: BeautifulSoup4 with requests
- **MCP Server**: FastMCP for AI tool integration
- **Error Handling**: Comprehensive logging and graceful failure handling