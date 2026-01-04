"""Detective Node - Searches for and discovers candidate homepages"""

import logging
from typing import Optional

from app.agents.state import AgentState
from app.agents.tools.search import search_scholar_homepage

logger = logging.getLogger(__name__)


def find_best_homepage_url(search_results: list, candidate_name: str, affiliation: str) -> Optional[str]:
    """
    Analyze search results and select the most likely homepage URL.
    
    Args:
        search_results: List of search results from DuckDuckGo
        candidate_name: Name of the candidate
        affiliation: Affiliation to match
        
    Returns:
        Best matching URL or None
    """
    if not search_results:
        return None
    
    # Scoring heuristics for URL selection
    best_url = None
    best_score = 0
    
    for result in search_results:
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        score = 0
        
        # Positive signals
        if any(keyword in url for keyword in ['homepage', 'personal', 'people', 'faculty', 'profile', '~']):
            score += 3
        
        if any(keyword in title for keyword in ['homepage', 'home page', 'personal page']):
            score += 2
        
        # University domain is good
        if any(domain in url for domain in ['.edu', '.ac.', affiliation.lower().replace(' ', '')[:10]]):
            score += 2
        
        # Name in URL is a strong signal
        name_parts = candidate_name.lower().split()
        if any(part in url for part in name_parts if len(part) > 2):
            score += 4
        
        # Negative signals
        if any(keyword in url for keyword in ['linkedin', 'facebook', 'twitter', 'instagram', 'wikipedia']):
            score -= 5
        
        if any(keyword in url for keyword in ['pdf', 'paper', 'publication', 'arxiv']):
            score -= 2
        
        if score > best_score:
            best_score = score
            best_url = result['url']
    
    return best_url


async def detective_node(state: AgentState) -> AgentState:
    """
    Node 3: Detective
    Searches for the current candidate's homepage using search engines.
    Processes one PENDING candidate at a time.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with search results
    """
    candidates = state["candidates"]
    current_index = state["current_index"]
    
    # Find next PENDING candidate
    while current_index < len(candidates):
        candidate = candidates[current_index]
        
        if candidate.status == "PENDING":
            logger.info(f"[DetectiveNode] Processing #{current_index}: {candidate.name}")
            
            # Search for homepage
            search_results = search_scholar_homepage(candidate.name, candidate.affiliation)
            
            if search_results:
                # Find the best matching URL
                best_url = find_best_homepage_url(search_results, candidate.name, candidate.affiliation)
                
                if best_url:
                    candidate.homepage = best_url
                    logger.info(f"[DetectiveNode] Found URL: {best_url}")
                else:
                    logger.warning(f"[DetectiveNode] No suitable URL found in search results")
                    candidate.status = "FAILED"
                    candidate.skip_reason = "No suitable homepage found in search results"
            else:
                logger.warning(f"[DetectiveNode] Search returned no results")
                candidate.status = "FAILED"
                candidate.skip_reason = "Search returned no results"
            
            # Move to next candidate
            state["current_index"] = current_index + 1
            return state
        
        current_index += 1
    
    # No more PENDING candidates
    logger.info("[DetectiveNode] No more PENDING candidates to process")
    state["current_index"] = current_index
    
    return state

