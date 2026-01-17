from typing import TypedDict, Annotated, List
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langgraph.graph import StateGraph, END
# Make sure to set your API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAMU0wzYEpMOEC6Zt7Xp0jUj4jve824e2o"

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


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)


def physical_evidence_node(state: CaseState):
    prompt = f"""You are a forensic scientist. Provide a CONCISE analysis (max 200 words).

    Physical Evidence: {state['Phy_Evi']}
    Case Context: {state['Inc_over']}

    Focus on: Key findings, significance, and connections to the case."""
    response = llm.invoke(prompt)
    report_text = response.content if hasattr(response, 'content') else str(response)
    return {"agent_reports": [f"PHYSICAL EVIDENCE REPORT: {report_text}"]}



def witness_agent_node(state: CaseState):
    # Logic for Witness Testimony Agent
    prompt = f"""Analyze witness statements CONCISELY (max 200 words).

    Witness Testimony: {state['wit_test']}
    Case Context: {state['Inc_over']}

    Focus on: Credibility, inconsistencies, and key details."""
    response = llm.invoke(prompt)
    report_text = response.content if hasattr(response, 'content') else str(response)
    return {"agent_reports": [f"WITNESS REPORT: {report_text}"]}


def timeline_agent_node(state: CaseState):
    """
    Expert agent focused on reconstructing the chronological order of events.
    """
    # Pulling data that impacts time
    overview = state["Inc_over"]
    witnesses = state["wit_test"]
    evidence = state["Phy_Evi"]

    prompt = f"""Create a CONCISE timeline (max 200 words).

    Incident: {overview}
    Witnesses: {witnesses}
    Evidence: {evidence}

    Provide:
    1. Key timeline events (bullet points)
    2. Any conflicts or gaps
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
builder.add_node("timeline_reconstruction", timeline_agent_node)

# 3. Define the Flow (The "Relay Race")
# This tells the system where to start and who to pass the folder to next.
builder.set_entry_point("physical_analysis")

builder.add_edge("physical_analysis", "witness_analysis")
builder.add_edge("witness_analysis", "timeline_reconstruction")

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
