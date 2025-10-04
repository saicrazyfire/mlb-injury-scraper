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

- **Multi-Team Support**: Scrapes injury data for all 30 MLB teams from MLB.com
- **Real-time Data**: Fetches current injury information in real-time
- **Team Configuration**: Configurable team URLs via `config.toml` file
- **Special Character Support**: Handles special characters in player names (e.g., Dedniel Núñez)
- **Chronological Order**: Maintains chronological order (most recent injuries first)
- **MCP Server Integration**: Serves data via FastMCP server for AI tool integration
- **Multiple Query Tools**: Provides various tools for different data views and team queries
- **Robust Error Handling**: Comprehensive logging and graceful failure handling
- **Backward Compatibility**: Legacy Mets-only methods still supported

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

#### Local Development
```bash
# Traditional MCP server with stdio transport (for local AI tools)
uv run mlb-injury-server

# MCP server with HTTP/SSE transport (for remote/web-based MCP clients)
uv run python server.py --sse

# Or specify custom host/port
uv run python server.py --sse --host 0.0.0.0 --port 8000
```

#### Using Docker

**Pull and run the pre-built image (MCP HTTP/SSE by default):**
```bash
docker run -p 8000:8000 ghcr.io/yourusername/mlb-injury-scraper:latest
```

**Run in stdio mode (for local integration):**
```bash
docker run -it ghcr.io/yourusername/mlb-injury-scraper:latest python server.py
```

**Build and run locally:**
```bash
# Build the image
docker build -t mlb-injury-scraper .

# Run with HTTP/SSE transport (default)
docker run -p 8000:8000 mlb-injury-scraper

# Run with stdio transport
docker run -it mlb-injury-scraper python server.py
```

**Using Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  mlb-injury-scraper:
    image: ghcr.io/yourusername/mlb-injury-scraper:latest
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## MCP Over HTTP/SSE Transport

The MCP server supports two transport protocols:

1. **stdio transport** (default): Traditional MCP over standard input/output for local AI tools
2. **HTTP/SSE transport** (`--sse` flag): MCP protocol over HTTP with Server-Sent Events for remote access

### Using HTTP/SSE Transport

The HTTP/SSE transport allows MCP clients to connect to the server over HTTP, making it accessible without local code execution. This is perfect for:
- Web-based MCP clients
- Remote deployments
- Cloud-hosted AI services
- Docker containers

**MCP Endpoint**: `http://localhost:8000/sse`

### Connecting MCP Clients

#### Python MCP Client:
```python
import asyncio
import httpx
from mcp.client.sse import sse_client
from mcp import ClientSession

async def connect_to_mlb_server():
    async with httpx.AsyncClient() as client:
        async with sse_client("http://localhost:8000/sse") as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                
                # Call a tool
                result = await session.call_tool("get_team_injuries", {"team": "mets"})
                return result

asyncio.run(connect_to_mlb_server())
```

#### Claude Desktop Configuration (HTTP/SSE):
```json
{
  "mcpServers": {
    "mlb-injury-scraper": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**Note**: The HTTP/SSE transport uses the standard MCP protocol, so all MCP tools work identically to stdio mode.

### Additional REST API (Optional)

In addition to the MCP protocol, a standalone REST API server is also available in `http_server.py` for non-MCP integrations:

```bash
# Run standalone REST API (not MCP-compatible)
uv run mlb-injury-http-server
```

This provides standard REST endpoints at:
- `GET /api/teams` - List all teams
- `GET /api/teams/{team}/injuries` - Get team injuries
- `GET /api/teams/{team}/summary` - Injury summary
- `GET /api/teams/{team}/players/{player_name}` - Search player
- `GET /docs` - Interactive API documentation

**Note**: The REST API and MCP server are separate services. Use MCP HTTP/SSE transport for MCP client compatibility.

### Example API Usage

#### Using curl:
```bash
# Get available teams
curl http://localhost:8000/api/teams

# Get Dodgers injuries
curl http://localhost:8000/api/teams/dodgers/injuries

# Get Yankees injury summary
curl http://localhost:8000/api/teams/yankees/summary

# Search for a player
curl http://localhost:8000/api/teams/mets/players/Pete

# Stream real-time updates (SSE)
curl -N http://localhost:8000/api/teams/mets/injuries/stream?interval=30
```

#### Using Python:
```python
import requests

# Basic API client
base_url = "http://localhost:8000"

# Get teams
teams = requests.get(f"{base_url}/api/teams").json()
print(f"Available teams: {teams['total_teams']}")

# Get team injuries
injuries = requests.get(f"{base_url}/api/teams/mets/injuries").json()
print(f"Mets injuries: {injuries['total_injured']}")

# For SSE streaming, see examples/http_client_example.py
```

#### Using JavaScript:
```javascript
// Fetch team data
const response = await fetch('http://localhost:8000/api/teams/dodgers/injuries');
const data = await response.json();
console.log(`${data.team_name} has ${data.total_injured} injured players`);

// Server-Sent Events for real-time updates
const eventSource = new EventSource('http://localhost:8000/api/teams/mets/injuries/stream?interval=30');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Injury update:', data);
};
```

### Response Formats

All endpoints return JSON responses with consistent structure:

```json
{
  "team": "mets",
  "team_name": "New York Mets", 
  "total_injured": 5,
  "players": [
    {
      "name": "Player Name",
      "position": "RHP",
      "injury": "Right elbow strain",
      "il_date": "June 15 (15-day IL)",
      "expected_return": "Late July",
      "status": "Progressing well in rehab",
      "last_updated": "July 10"
    }
  ]
}
```

### Running the HTTP Server

The HTTP server runs on port 8000 by default and provides:
- **REST API endpoints** for programmatic access
- **Server-Sent Events (SSE)** for real-time streaming
- **Interactive documentation** at `/docs`
- **CORS support** for web applications
- **Health checks** for monitoring

### MCP Tools Available

1. **get_team_injuries(team)** - Get complete injury report for any MLB team
2. **get_available_teams()** - Get list of all supported MLB teams  
3. **get_injury_summary(team)** - Get summary with counts and breakdowns for a team
4. **search_player_injury(player_name, team)** - Search for specific player on a team
5. **get_mets_injuries()** - Legacy method for Mets-only queries (backward compatibility)

#### Team Keys
Use these team keys when calling the tools:
- `mets`, `yankees`, `dodgers`, `astros`, `braves`, `phillies`, `padres`, `orioles`
- `rangers`, `marlins`, `giants`, `cubs`, `redsox`, `guardians`, `brewers`, `dbacks`
- `tigers`, `cardinals`, `twins`, `mariners`, `bluejays`, `rays`, `nationals`, `reds`
- `pirates`, `royals`, `angels`, `athletics`, `whitesox`, `rockies`

#### Examples
```python
# Get Dodgers injuries
get_team_injuries("dodgers")

# Get Yankees injury summary  
get_injury_summary("yankees")

# Search for a player on the Mets
search_player_injury("Pete Alonso", "mets")

# Get all available teams
get_available_teams()
```

## MCP Configuration

Add to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "mlb-injury-scraper": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/your/project/mlb-injury-scraper",
        "/path/to/your/project/mlb-injury-scraper/server.py"
      ]
    }
  }
}
```

**Important**: Replace `/path/to/your/project/mlb-injury-scraper` with the absolute path to your project directory.

## Configuration

The application uses a `config.toml` file to define MLB team URLs and metadata. This file contains:

- **Team URLs**: Direct links to each team's injury report page on MLB.com
- **Team Names**: Full team names (e.g., "New York Mets")
- **Abbreviations**: Standard MLB team abbreviations (e.g., "NYM")

### Adding New Teams

To add support for additional teams, edit the `config.toml` file:

```toml
[teams.newteam]
name = "New Team Name"
url = "https://www.mlb.com/news/newteam-injuries-and-roster-moves"
abbreviation = "NT"
```

The application will automatically pick up changes to the configuration file.

## Docker Images

Pre-built Docker images are automatically built and published to GitHub Container Registry on every release:

- **Latest stable**: `ghcr.io/yourusername/mlb-injury-scraper:latest`
- **Specific version**: `ghcr.io/yourusername/mlb-injury-scraper:v1.0.0`
- **Development**: `ghcr.io/yourusername/mlb-injury-scraper:main`

Images are built for both `linux/amd64` and `linux/arm64` platforms.

### CI/CD Pipeline

The project includes a GitHub Actions workflow that:
- Runs tests on every push and pull request
- Builds multi-platform Docker images
- Publishes images to GitHub Container Registry
- Creates attestations for supply chain security
- Supports semantic versioning with git tags

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