# 🚔 Detective Evidence Management System with AI Case Analysis

A full-stack web application for police departments to manage evidence and leverage AI agents for case analysis.

## 🎯 Features

### Evidence Management
- **Multi-category Evidence Upload**: Forensic data, witness testimony, images, documents, physical evidence, digital evidence, and audio/video
- **Snowflake Database Integration**: Cloud storage with local fallback
- **Real-time Evidence Tracking**: View, search, and filter evidence
- **File Upload Support**: Drag-and-drop interface with preview capabilities

### AI Case Analysis 🤖
- **Multi-Agent Analysis System**: Powered by LangGraph and Google Gemini
  - **Physical Evidence Agent**: Forensic analysis specialist
  - **Witness Testimony Agent**: Cross-references statements with case details
  - **Timeline Reconstruction Agent**: Builds chronological timelines and identifies conflicts
- **Comprehensive Reports**: Automated concluding reports with all findings
- **Real-time Processing**: Stream case data directly to AI agents

## 🏗️ Tech Stack

### Frontend
- HTML5, CSS3 (Police-themed UI)
- Vanilla JavaScript
- Responsive design with drag-and-drop

### Backend
- **Node.js + Express**: Evidence upload API (Port 3000)
- **Python + Flask**: AI Agent API (Port 5000)
- **Snowflake**: Cloud database (optional)

### AI/ML
- **LangGraph**: Agent orchestration
- **Google Gemini 1.5 Flash**: LLM for analysis
- **LangChain**: Agent framework

## 🚀 Setup Instructions

### 1. Install Dependencies

#### Node.js Dependencies
```bash
npm install
```

#### Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
# Snowflake Configuration (Optional - leave blank for local-only mode)
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USERNAME=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=EVIDENCE_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# Server Configuration
PORT=3000
```

### 3. Set Google API Key

Add your Google Gemini API key in `agents.py`:
```python
os.environ["GOOGLE_API_KEY"] = "your-actual-api-key-here"
```

Get your API key from: https://makersuite.google.com/app/apikey

### 4. Start the Servers

#### Terminal 1: Node.js Backend (Evidence Upload)
```bash
npm start
```
Server runs on: http://localhost:3000

#### Terminal 2: Python Agent API (AI Analysis)
```bash
python3 agent_api.py
```
API runs on: http://localhost:5000

### 5. Access the Application

- **Evidence Upload**: http://localhost:3000
- **AI Case Analysis**: http://localhost:3000/case-analysis.html

## 📋 Usage Guide

### Uploading Evidence

1. Navigate to http://localhost:3000
2. Enter case number
3. Select evidence category (sidebar)
4. Upload files (drag-and-drop or browse)
5. Fill in evidence details:
   - Description
   - Collected by (officer name)
   - Date/time collected
   - Location
6. Click "Submit Evidence"

**Note**: Only "Forensic Data" category saves to Snowflake (if configured). Other categories are local-only.

### Running AI Case Analysis

1. Click "🤖 AI Case Analysis" in the header
2. Fill in all required fields:
   - **Incident Overview**: What happened? When? Where?
   - **Targets/Suspects**: Names, descriptions, known info
   - **Physical Evidence**: Fingerprints, DNA, weapons, etc.
   - **Witness Testimony**: What witnesses saw/heard
   - **Leads**: Tips, connections, additional info
3. Click "🔍 Analyze Case with AI"
4. Wait for agents to process (Physical → Witness → Timeline)
5. Review individual agent reports
6. Read the concluding report

## 🤖 AI Agent Architecture

```
Case Data Input
    ↓
Physical Evidence Agent (Forensic Analysis)
    ↓
Witness Testimony Agent (Cross-reference)
    ↓
Timeline Reconstruction Agent (Chronology)
    ↓
Orchestrator (Generates Concluding Report)
    ↓
Final Report Output
```

### Agent Capabilities

- **Physical Evidence Agent**: Analyzes forensic data using scientific methodology
- **Witness Testimony Agent**: Cross-references statements, identifies inconsistencies
- **Timeline Agent**: Reconstructs event chronology, finds logical conflicts and missing windows

## 🔧 Dual-Mode Operation

### Snowflake Mode
- Configure `.env` with Snowflake credentials
- Evidence stored in `EVIDENCE_DB.PUBLIC.FORENSIC_EVIDENCE`
- Cloud-based, team-accessible

### Local Mode
- Leave Snowflake settings blank in `.env`
- Evidence stored in `./uploads` directory
- Automatic fallback if Snowflake unavailable

## 📡 API Endpoints

### Node.js Backend (Port 3000)
- `POST /api/evidence/forensic` - Upload forensic evidence
- `GET /api/snowflake/test` - Test database connection
- `GET /uploads/:filename` - Serve uploaded files

### Python Agent API (Port 5000)
- `POST /api/analyze-case` - Submit case for AI analysis
- `GET /health` - API health check

## 🔒 Security Notes

- `.env` file is git-ignored (use `.env.example` as template)
- Each team member maintains their own credentials
- File uploads are stored with timestamps
- CORS enabled for local development

## 🐛 Troubleshooting

### Server exits with code 137
Memory limit reached. Restart with:
```bash
lsof -ti:3000 | xargs kill -9 2>/dev/null; sleep 1; npm start
```

### Python import errors
Ensure packages installed to correct Python version:
```bash
which python3
python3 -m pip install -r requirements.txt
```

### AI Agent API not responding
Check Python server is running on port 5000:
```bash
python3 agent_api.py
```

### Snowflake connection failed
Check `.env` configuration or switch to local mode by leaving Snowflake fields blank.

## 📦 Project Structure

```
UFThacks2026/
├── index.html              # Main evidence upload page
├── case-analysis.html      # AI case analysis interface
├── styles.css              # Police-themed styling
├── script.js               # Frontend JavaScript
├── server.js               # Node.js backend
├── agents.py               # LangGraph agent definitions
├── agent_api.py            # Flask API for agents
├── package.json            # Node dependencies
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (git-ignored)
├── .env.example            # Template for .env
└── uploads/                # Local file storage
```

## 👥 Team Collaboration

Each developer should:
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Add their own Snowflake credentials (or leave blank for local mode)
4. Get their own Google API key for AI features
5. Never commit `.env` to git

## 📄 License

MIT License - Built for UFT Hacks 2026
