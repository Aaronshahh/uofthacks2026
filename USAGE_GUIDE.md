# 🚀 Quick Start Guide - AI Case Analysis System

## Overview
Your detective evidence management system now has **AI-powered case analysis**! The system uses three specialized AI agents that work together to analyze cases and generate comprehensive reports.

## 🎯 What's New

### AI Analysis Pipeline
```
User Input → Python Flask API → LangGraph Agents → Gemini AI → Final Report
```

### Three Specialized Agents
1. **Physical Evidence Agent** 🔬
   - Analyzes forensic data scientifically
   - Cross-references with incident overview

2. **Witness Testimony Agent** 👥
   - Reviews witness statements
   - Identifies inconsistencies
   - Cross-references with case details

3. **Timeline Reconstruction Agent** ⏰
   - Builds minute-by-minute timeline
   - Highlights logical conflicts
   - Identifies missing time windows

## 🚀 How to Start

### Option 1: Use the Start Script (Easiest)
```bash
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Node.js Evidence Server:**
```bash
npm start
```

**Terminal 2 - Python AI Agent API:**
```bash
python3 agent_api.py
```

## 📝 Step-by-Step Usage

### 1. Upload Evidence (Optional)
First, you can upload evidence files at `http://localhost:3000`:
- Forensic data
- Images/photos
- Documents
- Physical evidence descriptions
- Digital evidence
- Audio/video files

### 2. Run AI Case Analysis
Click the **"🤖 AI Case Analysis"** button in the header, or go directly to:
```
http://localhost:3000/case-analysis.html
```

### 3. Fill in Case Details

#### Required Fields:

**📋 Incident Overview**
```
Example:
"On January 15, 2026, at approximately 10:30 PM, a residential burglary
occurred at 123 Main Street. The homeowner reported missing jewelry
valued at $15,000. Point of entry was a broken rear window. No signs
of forced entry on the front door."
```

**🎯 Target(s) / Suspect(s)**
```
Example:
"John Doe, male, 5'10", brown hair, blue eyes. Last seen wearing
dark hoodie. Known associate of victim's ex-employee. Has prior
burglary convictions from 2020."
```

**🔬 Physical Evidence**
```
Example:
"- Fingerprints lifted from broken window frame
- Size 11 shoe prints in muddy backyard
- Blue fabric fibers found on window sill
- Cigarette butt near entry point (sent for DNA analysis)
- Tool marks on window frame consistent with crowbar"
```

**👥 Witness Testimony**
```
Example:
"Neighbor Jane Smith (Witness 1):
'I saw a dark sedan parked on the street around 10:15 PM.
I heard glass breaking around 10:30 PM but thought it was garbage trucks.'

Neighbor Bob Johnson (Witness 2):
'I was walking my dog at 10:25 PM and saw someone in a dark hoodie
running from the backyard. They got into a dark car and drove away quickly.'"
```

**🔗 Leads & Additional Information**
```
Example:
"- Victim recently fired employee who had keys to the house
- Similar burglaries reported in neighborhood last month
- Security camera from across the street may have footage
- Victim's ex-employee owns a dark blue sedan
- Pawn shops alerted about jewelry descriptions"
```

### 4. Submit for Analysis
Click **"🔍 Analyze Case with AI"**

The system will:
1. Send data to Python Flask API
2. Invoke LangGraph orchestrator
3. Run agents in sequence:
   - Physical Evidence Agent analyzes forensic data
   - Witness Testimony Agent cross-references statements
   - Timeline Agent reconstructs chronology
4. Generate concluding report

### 5. Review Results

You'll receive:
- **Individual Agent Reports**: Detailed analysis from each specialist
- **Concluding Report**: Comprehensive summary with:
  - Case overview
  - Target information
  - All agent findings
  - Investigation summary
  - Statistics

## 🔧 Architecture

### Frontend → Backend Flow
```
case-analysis.html (User fills form)
        ↓ (HTTP POST with JSON)
agent_api.py (Flask endpoint: /api/analyze-case)
        ↓
agents.py (detective_orchestrator.invoke())
        ↓
LangGraph StateGraph executes nodes:
  1. physical_evidence_node
  2. witness_agent_node
  3. timeline_agent_node
        ↓
Google Gemini 1.5 Flash (LLM analysis)
        ↓
Results collected in agent_reports[]
        ↓
generate_concluding_report()
        ↓ (HTTP Response JSON)
case-analysis.html displays results
```

### Data Flow
```javascript
// Frontend sends this JSON:
{
  "Inc_over": "incident description",
  "Targ": "target information",
  "Phy_Evi": "physical evidence",
  "wit_test": "witness testimony",
  "leads": "leads and tips"
}

// Backend returns this JSON:
{
  "success": true,
  "agent_reports": [
    "PHYSICAL EVIDENCE REPORT: ...",
    "WITNESS REPORT: ...",
    "CHRONOLOGICAL TIMELINE: ..."
  ],
  "concluding_report": "Full formatted report...",
  "case_state": { /* full state object */ }
}
```

## 🎨 UI Features

### Case Analysis Page
- **Dark Police Theme**: Matches evidence upload page
- **Required Field Validation**: Won't submit incomplete forms
- **Loading Animation**: Shows progress during analysis
- **Color-Coded Reports**: Each agent report in separate sections
- **Highlighted Concluding Report**: Final summary in gold-bordered box
- **Error Handling**: Clear error messages if API unavailable

## 🐛 Troubleshooting

### "Error: Make sure the AI Agent API is running on port 5000"
**Solution**: Start Python server:
```bash
python3 agent_api.py
```

### "Failed to fetch"
**Solution**: Check both servers are running:
```bash
# Check Node.js (port 3000)
lsof -ti:3000

# Check Python (port 5000)
lsof -ti:5000
```

### Agents not analyzing properly
**Solution**: Check Google API key in `agents.py`:
```python
os.environ["GOOGLE_API_KEY"] = "your-actual-key-here"
```

Get key from: https://makersuite.google.com/app/apikey

### Import errors in agents.py
**Solution**: Install Python dependencies:
```bash
pip install -r requirements.txt
```

## 📊 Example Output

After analysis, you'll see:

```
═══════════════════════════════════════════════
DETECTIVE CASE ANALYSIS - CONCLUDING REPORT
═══════════════════════════════════════════════

📋 CASE OVERVIEW:
[Your incident description]

🎯 TARGET(S):
[Your target information]

═══════════════════════════════════════════════
SPECIALIST ANALYSIS REPORTS
═══════════════════════════════════════════════

Report 1:
────────────────────────────────────────────────
PHYSICAL EVIDENCE REPORT: [Forensic analysis from AI]

Report 2:
────────────────────────────────────────────────
WITNESS REPORT: [Witness analysis from AI]

Report 3:
────────────────────────────────────────────────
CHRONOLOGICAL TIMELINE: [Timeline reconstruction from AI]

═══════════════════════════════════════════════
INVESTIGATION SUMMARY
═══════════════════════════════════════════════

📊 Total Specialist Reports: 3
🔍 Physical Evidence Analyzed: Yes
👥 Witness Testimony Reviewed: Yes
🔗 Leads Identified: Yes
```

## 🎯 Tips for Best Results

1. **Be Detailed**: More information = better analysis
2. **Use Specific Times**: Help the Timeline Agent
3. **Separate Witnesses**: Number each witness statement
4. **Include Evidence Details**: Describe forensic findings precisely
5. **List All Leads**: Even minor tips can be valuable

## 🔐 Security Notes

- Runs locally on your machine
- No data sent to external servers (except Google Gemini for AI)
- `.env` file keeps credentials private
- Each team member uses their own API keys

## 📚 Next Steps

1. Test with sample case data
2. Integrate with your evidence uploads
3. Export reports as PDFs (future feature)
4. Add more specialized agents (future feature)

## 💡 Pro Tips

- Keep both servers running during investigation
- Save interesting reports for reference
- Use clear, professional language in case descriptions
- The AI learns from context - more detail = better insights

---

**Need Help?** Check the main README: `AI_CASE_ANALYSIS_README.md`
