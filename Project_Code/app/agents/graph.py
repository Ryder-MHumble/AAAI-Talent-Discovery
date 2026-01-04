"""LangGraph Workflow Definition"""

from langgraph.graph import StateGraph, END
from typing import Literal
import logging

from app.agents.state import AgentState
from app.agents.nodes.ingestion import ingestion_node
from app.agents.nodes.filter import filter_node
from app.agents.nodes.detective import detective_node
from app.agents.nodes.auditor import auditor_node

logger = logging.getLogger(__name__)


def should_continue_processing(state: AgentState) -> Literal["detective", "complete"]:
    """
    Routing function to determine if we should continue processing or complete.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name or "complete"
    """
    candidates = state["candidates"]
    current_index = state["current_index"]
    
    # Check if there are any more PENDING candidates to process
    remaining = any(
        c.status == "PENDING" 
        for c in candidates[current_index:]
    )
    
    if remaining:
        logger.info(f"[Router] Continuing processing (index={current_index})")
        return "detective"
    else:
        logger.info("[Router] All candidates processed, completing")
        state["is_complete"] = True
        return "complete"


def create_agent_graph() -> StateGraph:
    """
    Create and return the agent workflow graph.
    
    Workflow:
    1. Ingestion -> Load candidates from AAAI
    2. Filter -> Mark non-target candidates as SKIPPED
    3. Detective -> Search for homepages (loops for each candidate)
    4. Auditor -> Verify and extract information
    5. Router -> Check if more candidates need processing
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("detective", detective_node)
    workflow.add_node("auditor", auditor_node)
    
    # Define edges
    workflow.set_entry_point("ingestion")
    
    # Ingestion -> Filter
    workflow.add_edge("ingestion", "filter")
    
    # Filter -> Detective (start processing)
    workflow.add_edge("filter", "detective")
    
    # Detective -> Auditor (after finding a URL)
    workflow.add_edge("detective", "auditor")
    
    # Auditor -> Router (check if more to process)
    workflow.add_conditional_edges(
        "auditor",
        should_continue_processing,
        {
            "detective": "detective",  # Loop back to process next candidate
            "complete": END
        }
    )
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("[Graph] Agent workflow compiled successfully")
    
    return app

