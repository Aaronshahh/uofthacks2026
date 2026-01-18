from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langgraph.graph import StateGraph, END
from RAG.rag_query import RAGQueryService, format_cases_for_display

'''
This class is the shared folder that all of the chatbots have access to,
from here very specific information is going to be passed to each gemini agent
which is then passed into their system prompt

the folder will contain:
-Incedent Overview:
-Targets
-Physicl Evidence: passed to the Physical Evidence Agent
-Witness Testimony
-leads

'''


class CaseState(TypedDict):

    '''
    Variables inside the caseState will be updated based on new information
    '''

    Inc_over: str       # Description from your Snowflake DB
    Targ: str           # frontend sending data to the agent directly
    agent_reports: Annotated[List[str], operator.add]  # A list where agents append their findings
    Phy_Evi: str
    wit_test: str
    leads: str
    evidence_image: Optional[bytes]  # Raw image bytes for physical evidence from frontend


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)

# Initialize RAG Query Service
rag_service = RAGQueryService()


def physical_evidence_node(state: CaseState):
    """
    Physical evidence analysis node with RAG retrieval.
    Searches for similar cases in the database based on evidence image.
    """
    rag_context = ""
    
    # If evidence image is provided, retrieve similar cases from database
    if state.get('evidence_image'):
        print(f"📸 Evidence image detected: {len(state['evidence_image'])} bytes")
        try:
            print("🔍 Querying RAG service for similar cases...")
            rag_result = rag_service.query(state['evidence_image'])
            rag_context = format_cases_for_display(rag_result)
            print(f"✅ RAG retrieval successful: {len(rag_result.cases)} cases found")
        except Exception as e:
            print(f"❌ RAG retrieval failed: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            rag_context = f"Note: RAG retrieval failed ({str(e)}). Proceeding with case analysis."
    else:
        print("⚠️ No evidence image provided - skipping RAG retrieval")
    
    print(f"\n--- RAG Context ---\n{rag_context}\n-------------------\n")

    prompt = f"""You are a forensic evidence specialist assisting an investigation team.
Your role is to analyze physical evidence objectively and conservatively,
mirroring real-world forensic practice.

Provide a CONCISE analysis (max 200 words). Do NOT speculate beyond the data provided.
Do NOT assert guilt, motive, or causality.

    Physical Evidence: {state['Phy_Evi']}
    Case Context: {state['Inc_over']}
    
    Similar Cases from Database:
    {rag_context if rag_context else 'No similar cases found in database.'}

    Your analysis should include:
- Observable forensic characteristics and measurable details
- Forensic significance and limitations of the evidence
- Notable consistencies or inconsistencies with the case context
- High-level comparison to similar historical cases (if provided)
- Clear separation between direct observations and inferred possibilities

When referencing historical cases, explicitly indicate that they are comparative, not determinative.
Maintain traceability to the provided inputs.     
"""
    response = llm.invoke(prompt)
    report_text = response.content if hasattr(response, 'content') else str(response)
    return {"agent_reports": [f"PHYSICAL EVIDENCE REPORT: {report_text}"]}



def witness_agent_node(state: CaseState):
    # Logic for Witness Testimony Agent
    prompt = f"""
    You are an investigative analyst specializing in witness testimony evaluation.
    Your role is to assess statements objectively, without assuming intent, truthfulness, or deception.

    Provide a CONCISE analysis (max 200 words).
    Do NOT assert guilt, motive, or factual certainty.
    Avoid psychological speculation beyond observable statement characteristics.
    Witness Testimony: {state['wit_test']}
    Case Context: {state['Inc_over']}

    Your analysis should address:
    - Consistencies and inconsistencies across witness statements
    - Alignment or conflicts with known case context
    - Clarity, specificity, and temporal coherence of accounts
    - Potential sources of uncertainty (e.g., timing, vantage point, stress, second-hand information)

    Clearly distinguish between:
    - Directly stated observations
    - Uncertainties or contradictions
    - Analytical notes for follow-up investigation

    Maintain neutral, professional language suitable for investigative review.
    """
    response = llm.invoke(prompt)
    report_text = response.content if hasattr(response, 'content') else str(response)
    return {"agent_reports": [f"WITNESS REPORT: {report_text}"]}


def sketch_artist_node(state: CaseState):
    """
    Sketch artist agent that extracts suspect descriptions from witness testimonies.
    """
    witnesses = state["wit_test"]
    
    prompt = f"""You are a police sketch artist. Analyze witness testimonies and extract CONCISE physical descriptions of the suspect (max 200 words).

    Witness Testimony: {witnesses}

    Extract and organize:
    1. Physical features (height, build, age, race/ethnicity)
    2. Facial features (eyes, nose, hair, facial hair, distinctive marks)
    3. Clothing and accessories
    4. Any unique identifiers or distinguishing characteristics
    
    Focus only on suspect descriptions. Ignore other details."""
    
    response = llm.invoke(prompt)
    report_text = response.content if hasattr(response, 'content') else str(response)
    
    # Print to console
    print(f"\n{'='*60}")
    print(f"SKETCH ARTIST REPORT")
    print(f"{'='*60}")
    print(report_text)
    print(f"{'='*60}\n")
    
    return {"agent_reports": [f"SKETCH ARTIST REPORT: {report_text}"]}


def timeline_agent_node(state: CaseState):
    """
    Expert agent focused on reconstructing the chronological order of events.
    """
    # Pulling data that impacts time
    overview = state["Inc_over"]
    witnesses = state["wit_test"]
    evidence = state["Phy_Evi"]

    prompt = f"""

    You are an investigative timeline analyst responsible for reconstructing the chronological sequence of events in a case.

    Your task is to organize events objectively based only on the provided information.
    Do NOT infer intent, motive, or causality beyond explicit statements.

    Provide a CONCISE timeline analysis (max 200 words).

    Incident: {overview}
    Witnesses: {witnesses}
    Evidence: {evidence}

    Your output should include:
    - A chronological ordering of key events with timestamps or time ranges (if available)
    - Clear attribution of each event to its source (overview vs witness)
    - Identification of temporal gaps, ambiguities, or conflicts
    - Notes on events with uncertain or approximate timing

    Explicitly distinguish between:
    - Confirmed events
    - Disputed or conflicting accounts
    - Estimated or inferred timing (label clearly)

    Maintain neutral, investigator-grade language suitable for early-stage case analysis.
"""

    response = llm.invoke(prompt)

    report_text = response.content if hasattr(response, 'content') else str(response)
    return {"agent_reports": [f"TIMELINE REPORT: {report_text}"]}


# 1. Initialize the Graph using your CaseState structure
builder = StateGraph(CaseState)

# 2. Register your Nodes
# The first string is the "Name" of the room, the second is the function you wrote.
builder.add_node("physical_analysis", physical_evidence_node)
builder.add_node("witness_analysis", witness_agent_node)
builder.add_node("sketch_artist", sketch_artist_node)
builder.add_node("timeline_reconstruction", timeline_agent_node)

# 3. Define the Flow (The "Relay Race")
# This tells the system where to start and who to pass the folder to next.
builder.set_entry_point("physical_analysis")

builder.add_edge("physical_analysis", "witness_analysis")
builder.add_edge("witness_analysis", "sketch_artist")
builder.add_edge("sketch_artist", "timeline_reconstruction")

# 4. Define the Exit
# After the timeline is done, the case is "closed."
builder.add_edge("timeline_reconstruction", END)

# 5. Compile the Graph
# This creates the 'runnable' object you will call from your frontend.
detective_orchestrator = builder.compile()


'''
We would call this file by using detective_orchestrator.invoke(data)

data is the information in the case state

'''
