"""Ingestion Node - Fetches and parses AAAI-26 candidate data"""

import httpx
from bs4 import BeautifulSoup
from typing import List
import logging

from app.agents.state import AgentState
from app.api.models import CandidateProfile
from app.core.config import settings

logger = logging.getLogger(__name__)


# Mock data for DEV environment
MOCK_CANDIDATES = [
    CandidateProfile(
        name="Haoyang Li",
        affiliation="Carnegie Mellon University",
        role="Invited Speaker",
        status="PENDING"
    ),
    CandidateProfile(
        name="Yi Wu",
        affiliation="Google DeepMind",
        role="Technical Track",
        status="PENDING"
    ),
    CandidateProfile(
        name="Jie Tang",
        affiliation="Tsinghua University",
        role="Invited Speaker",
        status="PENDING"
    ),
    CandidateProfile(
        name="Xiaojun Chang",
        affiliation="University of Sydney",
        role="Technical Track",
        status="PENDING"
    ),
    CandidateProfile(
        name="Lei Chen",
        affiliation="Hong Kong University of Science and Technology",
        role="Invited Speaker",
        status="PENDING"
    ),
]


async def scrape_aaai_page(url: str) -> List[CandidateProfile]:
    """
    Scrape AAAI website to extract candidate information.
    
    Args:
        url: AAAI page URL
        
    Returns:
        List of CandidateProfile objects
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # This is a placeholder parser - actual implementation would depend on AAAI's HTML structure
            # Look for common patterns like:
            # - <h3> or <h4> tags for names
            # - Adjacent <p> or <span> for affiliations
            
            # Example parsing logic (adapt based on actual HTML structure)
            for item in soup.find_all(['div', 'li'], class_=['speaker', 'author', 'participant']):
                name = None
                affiliation = None
                
                # Try to extract name
                name_tag = item.find(['h3', 'h4', 'strong', 'b'])
                if name_tag:
                    name = name_tag.get_text(strip=True)
                
                # Try to extract affiliation
                aff_tag = item.find(['p', 'span', 'em'], class_=['affiliation', 'institution'])
                if aff_tag:
                    affiliation = aff_tag.get_text(strip=True)
                
                if name and affiliation:
                    candidates.append(CandidateProfile(
                        name=name,
                        affiliation=affiliation,
                        role="Invited Speaker" if "invited" in url.lower() else "Technical Track",
                        status="PENDING"
                    ))
        
        logger.info(f"Scraped {len(candidates)} candidates from {url}")
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
    
    return candidates


async def ingestion_node(state: AgentState) -> AgentState:
    """
    Node 1: Ingestion
    Fetches AAAI-26 data and populates the candidates list.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with candidates populated
    """
    logger.info(f"[IngestionNode] Starting for job_id={state['job_id']}")
    
    candidates = []
    
    if settings.APP_ENV == "DEV":
        # Use mock data in development
        logger.info("[IngestionNode] Using mock data (DEV mode)")
        candidates = MOCK_CANDIDATES.copy()
    else:
        # Scrape real AAAI pages in production
        logger.info("[IngestionNode] Scraping AAAI pages (PROD mode)")
        
        invited_speakers = await scrape_aaai_page(settings.AAAI_INVITED_SPEAKERS_URL)
        technical_track = await scrape_aaai_page(settings.AAAI_TECHNICAL_TRACK_URL)
        
        candidates = invited_speakers + technical_track
    
    state["candidates"] = candidates
    state["current_index"] = 0
    state["is_complete"] = False
    
    logger.info(f"[IngestionNode] Loaded {len(candidates)} candidates")
    
    return state

