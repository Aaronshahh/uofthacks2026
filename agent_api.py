from flask import Flask, request, jsonify
from flask_cors import CORS
from agents import detective_orchestrator, CaseState
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

@app.route('/api/analyze-case', methods=['POST'])
def analyze_case():
    """
    Endpoint to receive case data and invoke the LangGraph agents.

    Expected JSON payload:
    {
        "Inc_over": "Incident overview text",
        "Targ": "Target information",
        "Phy_Evi": "Physical evidence description",
        "wit_test": "Witness testimony",
        "leads": "Leads information"
    }
    """
    try:
        data = request.json

        # Validate required fields
        required_fields = ['Inc_over', 'Targ', 'Phy_Evi', 'wit_test', 'leads']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Prepare the initial case state
        initial_state = {
            'Inc_over': data['Inc_over'],
            'Targ': data['Targ'],
            'Phy_Evi': data['Phy_Evi'],
            'wit_test': data['wit_test'],
            'leads': data['leads'],
            'agent_reports': []  # Will be populated by agents
        }

        print(f"\n🔍 Processing case analysis...")
        print(f"Incident: {data['Inc_over'][:100]}...")

        # Invoke the detective orchestrator
        result = detective_orchestrator.invoke(initial_state)

        # Extract all agent reports
        agent_reports = result.get('agent_reports', [])

        # Generate concluding report
        concluding_report = generate_concluding_report(
            initial_state,
            agent_reports
        )

        print(f"✅ Analysis complete - {len(agent_reports)} reports generated")

        return jsonify({
            'success': True,
            'agent_reports': agent_reports,
            'concluding_report': concluding_report,
            'case_state': result
        })

    except Exception as e:
        print(f"❌ Error processing case: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_concluding_report(initial_state, agent_reports):
    """
    Generate a final concluding report based on all agent findings.
    """
    report_sections = []

    # Header
    report_sections.append("=" * 80)
    report_sections.append("DETECTIVE CASE ANALYSIS - CONCLUDING REPORT")
    report_sections.append("=" * 80)
    report_sections.append("")

    # Case Overview
    report_sections.append("📋 CASE OVERVIEW:")
    report_sections.append(initial_state['Inc_over'])
    report_sections.append("")

    # Target Information
    report_sections.append("🎯 TARGET(S):")
    report_sections.append(initial_state['Targ'])
    report_sections.append("")

    # Agent Findings
    report_sections.append("=" * 80)
    report_sections.append("SPECIALIST ANALYSIS REPORTS")
    report_sections.append("=" * 80)
    report_sections.append("")

    for i, report in enumerate(agent_reports, 1):
        report_sections.append(f"Report {i}:")
        report_sections.append("-" * 80)
        report_sections.append(report)
        report_sections.append("")

    # Summary
    report_sections.append("=" * 80)
    report_sections.append("INVESTIGATION SUMMARY")
    report_sections.append("=" * 80)
    report_sections.append("")
    report_sections.append(f"📊 Total Specialist Reports: {len(agent_reports)}")
    report_sections.append(f"🔍 Physical Evidence Analyzed: Yes" if initial_state['Phy_Evi'] else "No")
    report_sections.append(f"👥 Witness Testimony Reviewed: Yes" if initial_state['wit_test'] else "No")
    report_sections.append(f"🔗 Leads Identified: Yes" if initial_state['leads'] else "No")
    report_sections.append("")
    report_sections.append("=" * 80)
    report_sections.append("END OF REPORT")
    report_sections.append("=" * 80)

    return "\n".join(report_sections)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Detective Agent API'})


if __name__ == '__main__':
    print("\n🤖 Detective Agent API Server Starting...")
    print("🔗 API will be available at http://localhost:5000")
    print("📡 Endpoint: POST /api/analyze-case")
    print("━" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
