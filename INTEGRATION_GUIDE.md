# MLB Injury Scraper Integration Guide

This guide provides step-by-step instructions for integrating the MLB Injury Scraper with n8n and Microsoft Copilot Studio.

## Table of Contents
- [n8n Integration](#n8n-integration)
- [Microsoft Copilot Studio Integration](#microsoft-copilot-studio-integration)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

---

## n8n Integration

### Prerequisites
- n8n instance (cloud or self-hosted)
- Access to the MLB Injury Scraper API endpoint
- Basic understanding of n8n workflows

### Method 1: Direct HTTP Requests

#### Step 1: Create HTTP Request Node
```json
{
  "nodes": [
    {
      "parameters": {
        "url": "http://your-server:port/api/mets-injuries",
        "options": {
          "timeout": 10000
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [250, 300],
      "name": "Get Mets Injuries"
    }
  ]
}
```

#### Step 2: Process the Data
Add a **Code** node to process the injury data:

```javascript
// Process MLB injury data
const injuries = $input.all()[0].json;

const processedData = injuries.map(player => ({
  playerName: player.name,
  position: player.position,
  injury: player.injury,
  ilDate: player.il_date,
  expectedReturn: player.expected_return,
  status: player.status,
  lastUpdated: player.last_updated,
  severity: determineSeverity(player.expected_return),
  daysOnIL: calculateDaysOnIL(player.il_date)
}));

function determineSeverity(expectedReturn) {
  if (!expectedReturn) return 'Unknown';
  if (expectedReturn.toLowerCase().includes('day to day')) return 'Minor';
  if (expectedReturn.includes('2026') || expectedReturn.includes('season')) return 'Major';
  return 'Moderate';
}

function calculateDaysOnIL(ilDate) {
  if (!ilDate) return null;
  // Extract date and calculate days
  const dateMatch = ilDate.match(/(\w+)\s+(\d+)/);
  if (dateMatch) {
    const [, month, day] = dateMatch;
    const currentDate = new Date();
    const ilDateObj = new Date(`${month} ${day}, ${currentDate.getFullYear()}`);
    const diffTime = Math.abs(currentDate - ilDateObj);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
  return null;
}

return processedData;
```

#### Step 3: Create Workflow Triggers

**Schedule Trigger** for regular updates:
```json
{
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "hours",
          "hoursInterval": 6
        }
      ]
    }
  },
  "type": "n8n-nodes-base.scheduleTrigger",
  "name": "Every 6 Hours"
}
```

**Webhook Trigger** for on-demand requests:
```json
{
  "parameters": {
    "path": "mets-injuries",
    "options": {
      "responseMode": "responseNode"
    }
  },
  "type": "n8n-nodes-base.webhook",
  "name": "Injury Data Webhook"
}
```

### Method 2: Custom n8n Node

Create a custom node for reusable functionality:

```javascript
// nodes/MlbInjuryScraper/MlbInjuryScraper.node.ts
import { IExecuteFunctions } from 'n8n-core';
import {
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
  NodeOperationError,
} from 'n8n-workflow';

export class MlbInjuryScraper implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'MLB Injury Scraper',
    name: 'mlbInjuryScraper',
    group: ['transform'],
    version: 1,
    description: 'Fetch MLB injury data',
    defaults: {
      name: 'MLB Injury Scraper',
    },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        options: [
          {
            name: 'Get All Injuries',
            value: 'getAllInjuries',
          },
          {
            name: 'Get Injury Summary',
            value: 'getSummary',
          },
          {
            name: 'Search Player',
            value: 'searchPlayer',
          },
        ],
        default: 'getAllInjuries',
      },
      {
        displayName: 'Player Name',
        name: 'playerName',
        type: 'string',
        displayOptions: {
          show: {
            operation: ['searchPlayer'],
          },
        },
        default: '',
        placeholder: 'Enter player name',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];
    const operation = this.getNodeParameter('operation', 0) as string;

    for (let i = 0; i < items.length; i++) {
      try {
        let responseData;
        
        switch (operation) {
          case 'getAllInjuries':
            responseData = await this.helpers.request({
              method: 'POST',
              url: 'http://localhost:8000/mcp/call',
              body: {
                method: 'get_mets_injuries',
                params: {}
              },
              json: true,
            });
            break;
            
          case 'getSummary':
            responseData = await this.helpers.request({
              method: 'POST',
              url: 'http://localhost:8000/mcp/call',
              body: {
                method: 'get_injury_summary',
                params: {}
              },
              json: true,
            });
            break;
            
          case 'searchPlayer':
            const playerName = this.getNodeParameter('playerName', i) as string;
            responseData = await this.helpers.request({
              method: 'POST',
              url: 'http://localhost:8000/mcp/call',
              body: {
                method: 'search_player_injury',
                params: { player_name: playerName }
              },
              json: true,
            });
            break;
            
          default:
            throw new NodeOperationError(this.getNode(), `Unknown operation: ${operation}`);
        }

        returnData.push({
          json: responseData,
        });
      } catch (error) {
        if (this.continueOnFail()) {
          returnData.push({
            json: { error: error.message },
          });
          continue;
        }
        throw error;
      }
    }

    return [returnData];
  }
}
```

---

## Microsoft Copilot Studio Integration

### Prerequisites
- Microsoft Copilot Studio access
- Power Platform environment
- Custom connector capability

### Step 1: Create Custom Connector

#### Connector Definition
```json
{
  "swagger": "2.0",
  "info": {
    "title": "MLB Injury Scraper",
    "description": "Get MLB injury data for the New York Mets",
    "version": "1.0"
  },
  "host": "your-server.com",
  "basePath": "/api",
  "schemes": ["https"],
  "consumes": ["application/json"],
  "produces": ["application/json"],
  "paths": {
    "/mets-injuries": {
      "get": {
        "summary": "Get all Mets injuries",
        "description": "Retrieve complete injury report for NY Mets players",
        "operationId": "GetMetsInjuries",
        "responses": {
          "200": {
            "description": "Success",
            "schema": {
              "type": "array",
              "items": {
                "$ref": "#/definitions/InjuredPlayer"
              }
            }
          }
        }
      }
    },
    "/mets-injuries/summary": {
      "get": {
        "summary": "Get injury summary",
        "description": "Get summary statistics of Mets injuries",
        "operationId": "GetInjurySummary",
        "responses": {
          "200": {
            "description": "Success",
            "schema": {
              "$ref": "#/definitions/InjurySummary"
            }
          }
        }
      }
    },
    "/mets-injuries/search": {
      "get": {
        "summary": "Search for player injury",
        "description": "Search for specific player's injury information",
        "operationId": "SearchPlayerInjury",
        "parameters": [
          {
            "name": "playerName",
            "in": "query",
            "required": true,
            "type": "string",
            "description": "Name of the player to search for"
          }
        ],
        "responses": {
          "200": {
            "description": "Success",
            "schema": {
              "$ref": "#/definitions/PlayerSearchResult"
            }
          }
        }
      }
    }
  },
  "definitions": {
    "InjuredPlayer": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "position": {"type": "string"},
        "injury": {"type": "string"},
        "il_date": {"type": "string"},
        "expected_return": {"type": "string"},
        "status": {"type": "string"},
        "last_updated": {"type": "string"}
      }
    },
    "InjurySummary": {
      "type": "object",
      "properties": {
        "total_injured_players": {"type": "integer"},
        "injury_type_breakdown": {"type": "object"},
        "last_updated": {"type": "string"}
      }
    },
    "PlayerSearchResult": {
      "type": "object",
      "properties": {
        "found": {"type": "boolean"},
        "name": {"type": "string"},
        "position": {"type": "string"},
        "injury": {"type": "string"},
        "il_date": {"type": "string"},
        "expected_return": {"type": "string"},
        "status": {"type": "string"},
        "last_updated": {"type": "string"},
        "message": {"type": "string"}
      }
    }
  }
}
```

### Step 2: Create Copilot Actions

#### Action 1: Get Injury Report
```yaml
# Action: GetInjuryReport
Name: Get Mets Injury Report
Description: Retrieve the latest injury report for NY Mets players

Input Parameters: None

Output: 
- List of injured players with details
- Injury status and expected return dates
- Last updated information

Power Fx Formula:
```
Set(InjuryData, 'MLB Injury Scraper'.GetMetsInjuries());
Set(InjuryText, 
    Concat(InjuryData, 
        $"**{name}** ({position})" & Char(10) &
        $"Injury: {injury}" & Char(10) &
        If(!IsBlank(il_date), $"IL Date: {il_date}" & Char(10), "") &
        If(!IsBlank(expected_return), $"Expected Return: {expected_return}" & Char(10), "") &
        If(!IsBlank(last_updated), $"Last Updated: {last_updated}" & Char(10), "") &
        Char(10) & "---" & Char(10)
    )
);
InjuryText
```

#### Action 2: Search Player Injury
```yaml
# Action: SearchPlayerInjury
Name: Search Player Injury Status
Description: Search for a specific player's injury information

Input Parameters:
- PlayerName (Text): Name of the player to search for

Power Fx Formula:
```
Set(SearchResult, 'MLB Injury Scraper'.SearchPlayerInjury({playerName: Topic.PlayerName}));
If(SearchResult.found,
    $"**{SearchResult.name}** ({SearchResult.position})" & Char(10) &
    $"Injury: {SearchResult.injury}" & Char(10) &
    If(!IsBlank(SearchResult.il_date), $"IL Date: {SearchResult.il_date}" & Char(10), "") &
    If(!IsBlank(SearchResult.expected_return), $"Expected Return: {SearchResult.expected_return}" & Char(10), "") &
    If(!IsBlank(SearchResult.status), $"Status: {SearchResult.status}" & Char(10), "") &
    If(!IsBlank(SearchResult.last_updated), $"Last Updated: {SearchResult.last_updated}", ""),
    $"No injury information found for {Topic.PlayerName}"
)
```

### Step 3: Create Conversation Topics

#### Topic: Injury Report Request
```yaml
Name: Get Injury Report
Trigger Phrases:
- "Show me the Mets injury report"
- "Who's injured on the Mets?"
- "Current Mets injuries"
- "Injury list"

Conversation Flow:
1. Trigger: User asks for injury report
2. Action: Call GetInjuryReport action
3. Response: Display formatted injury information
4. Follow-up: Ask if user wants details on specific player

Message Node:
"Here's the current New York Mets injury report:

{x:InjuryReportText}

Would you like more details about any specific player?"
```

#### Topic: Player Search
```yaml
Name: Search Player Injury
Trigger Phrases:
- "How is [player name] doing?"
- "Is [player name] injured?"
- "When will [player name] return?"
- "Status of [player name]"

Conversation Flow:
1. Trigger: User asks about specific player
2. Entity Extraction: Extract player name
3. Action: Call SearchPlayerInjury action
4. Response: Display player-specific information

Message Node:
"Here's the latest information on {Topic.PlayerName}:

{x:PlayerInjuryInfo}

Is there anything else you'd like to know about the Mets injury situation?"
```

### Step 4: Advanced Features

#### Proactive Notifications
```yaml
# Power Automate Flow for Daily Updates
Trigger: Recurrence (Daily at 9 AM)
Action 1: HTTP Request to MLB Injury Scraper
Action 2: Parse JSON response
Action 3: Check for new injuries (compare with previous day)
Action 4: Send Teams/Email notification if changes detected

Condition: If new injuries or status changes
True Branch: Send notification
False Branch: Log "No changes"
```

#### Analytics Integration
```yaml
# Track injury trends
Power BI Dataset Connection:
- Connect to MLB Injury Scraper API
- Schedule daily refresh
- Create visualizations:
  * Injury timeline
  * Player availability trends
  * Recovery time analysis
  * Position-based injury patterns
```

---

## Common Use Cases

### 1. Fantasy Baseball Assistant
```javascript
// n8n workflow for fantasy advice
const injuries = await getInjuries();
const fantasyAdvice = injuries.map(player => ({
  player: player.name,
  position: player.position,
  recommendation: getFantasyRecommendation(player),
  alternativePickups: suggestAlternatives(player.position)
}));

function getFantasyRecommendation(player) {
  if (player.expected_return === 'Day to day') return 'Hold - likely to return soon';
  if (player.expected_return.includes('2026')) return 'Drop - out for season';
  return 'Monitor - uncertain timeline';
}
```

### 2. News Alert System
```yaml
# Copilot Studio topic for breaking injury news
Name: Injury Alerts
Description: Notify users of new injuries or status changes

Trigger: Scheduled check every 2 hours
Logic: Compare current data with cached previous data
Action: Send alert if changes detected
```

### 3. Team Management Dashboard
```javascript
// n8n workflow for team management
const summary = await getInjurySummary();
const dashboard = {
  totalInjured: summary.total_injured_players,
  byPosition: summary.injury_type_breakdown,
  criticalInjuries: injuries.filter(p => p.expected_return.includes('2026')),
  returningThisWeek: injuries.filter(p => p.expected_return.includes('day to day'))
};
```

---

## Troubleshooting

### Common Issues

#### n8n Connection Problems
```javascript
// Test connection node
try {
  const response = await this.helpers.request({
    method: 'GET',
    url: 'http://your-server:port/health',
    timeout: 5000
  });
  console.log('Connection successful:', response);
} catch (error) {
  console.error('Connection failed:', error.message);
}
```

#### Copilot Studio Authentication
```yaml
# Custom connector authentication
Authentication Type: API Key
Parameter Name: X-API-Key
Parameter Location: Header
```

#### Data Format Issues
```javascript
// Data validation function
function validateInjuryData(data) {
  const required = ['name', 'position', 'injury'];
  return data.every(player => 
    required.every(field => player[field] && player[field].trim())
  );
}
```

### Performance Optimization

#### Caching Strategy
```javascript
// n8n caching implementation
const cacheKey = 'mets_injuries_' + new Date().toDateString();
let cachedData = await this.helpers.getCredentials('cache').get(cacheKey);

if (!cachedData) {
  cachedData = await fetchInjuryData();
  await this.helpers.getCredentials('cache').set(cacheKey, cachedData, 3600); // 1 hour TTL
}

return cachedData;
```

#### Rate Limiting
```yaml
# Copilot Studio rate limiting
Max Requests: 100 per hour
Retry Logic: Exponential backoff
Error Handling: Graceful degradation with cached data
```

---

## Support and Maintenance

### Monitoring
- Set up health checks for the scraper endpoint
- Monitor API response times and error rates
- Track data freshness and accuracy

### Updates
- Regularly test integrations after MLB website changes
- Update connector definitions as needed
- Maintain documentation and examples

### Best Practices
- Implement proper error handling
- Use caching to reduce API calls
- Validate data before processing
- Provide meaningful user feedback
- Log important events for debugging