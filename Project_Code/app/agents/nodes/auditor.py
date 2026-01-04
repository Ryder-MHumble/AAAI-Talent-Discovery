"""Auditor Node - Verifies candidate homepages and extracts information"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict

from app.agents.state import AgentState
from app.agents.tools.verify import check_url_connectivity, fetch_page_text, semantic_match, extract_email_simple
from app.core.llm import get_llm
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


# LLM Prompt for Profile Extraction
PROFILE_EXTRACTION_PROMPT = """You are an expert HR researcher.
I will provide the text content of a scholar's homepage.
You must extract the following fields into JSON format:

- `name_cn`: Chinese name characters (e.g., "张三"). Return null if not found.
- `email`: Email address. Return null if not found.
- `bachelor_univ`: The university where they obtained their Bachelor's/Undergraduate degree. Look for "B.S.", "B.E.", "Bachelor", "Undergraduate". Return null if not found.
- `is_verified`: boolean. True if the page explicitly mentions the affiliation "{affiliation}".

Input Name: {name}
Input Affiliation: {affiliation}

Page Content:
{page_text}

Return ONLY a valid JSON object with these 4 fields. No additional text or explanation.
"""


async def extract_profile_with_llm(
    page_text: str, 
    name: str, 
    affiliation: str
) -> Optional[Dict]:
    """
    Use LLM to extract structured information from homepage text.
    
    Args:
        page_text: Text content from the homepage
        name: Candidate's name
        affiliation: Expected affiliation
        
    Returns:
        Dictionary with extracted fields or None if extraction fails
    """
    try:
        llm = get_llm()
        
        prompt = ChatPromptTemplate.from_template(PROFILE_EXTRACTION_PROMPT)
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "name": name,
            "affiliation": affiliation,
            "page_text": page_text[:8000]  # Limit to avoid token overflow
        })
        
        # Parse LLM response as JSON
        content = response.content
        
        # Try to extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        extracted = json.loads(content.strip())
        
        logger.info(f"[AuditorNode] LLM extracted: {extracted}")
        return extracted
        
    except Exception as e:
        logger.error(f"[AuditorNode] LLM extraction failed: {str(e)}")
        return None


async def auditor_node(state: AgentState) -> AgentState:
    """
    Node 4: Auditor
    Performs binary verification on candidates with homepage URLs.
    Uses LLM to extract additional information if verified.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with verification results
    """
    candidates = state["candidates"]
    
    # Find candidates that need auditing (have homepage but not yet verified/failed)
    for idx, candidate in enumerate(candidates):
        if candidate.homepage and candidate.status == "PENDING":
            logger.info(f"[AuditorNode] Verifying #{idx}: {candidate.name} -> {candidate.homepage}")
            
            # Step 1: Check connectivity
            is_accessible, status_code = await check_url_connectivity(candidate.homepage)
            
            if not is_accessible:
                logger.warning(f"[AuditorNode] URL not accessible (status {status_code})")
                candidate.status = "FAILED"
                candidate.skip_reason = f"Homepage not accessible (HTTP {status_code})"
                candidate.verification_time = datetime.now()
                continue
            
            # Step 2: Fetch page content
            page_text = await fetch_page_text(candidate.homepage)
            
            if not page_text:
                logger.warning(f"[AuditorNode] Failed to fetch page text")
                candidate.status = "FAILED"
                candidate.skip_reason = "Could not extract page content"
                candidate.verification_time = datetime.now()
                continue
            
            # Step 3: Semantic matching
            is_match = semantic_match(page_text, candidate.name, candidate.affiliation)
            
            if not is_match:
                logger.warning(f"[AuditorNode] Page content does not match candidate")
                candidate.status = "FAILED"
                candidate.skip_reason = "Page content does not match name/affiliation"
                candidate.verification_time = datetime.now()
                continue
            
            # Step 4: VERIFIED - Extract additional info with LLM
            logger.info(f"[AuditorNode] ✓ VERIFIED: {candidate.name}")
            candidate.status = "VERIFIED"
            
            # Extract simple email first (fallback)
            candidate.email = extract_email_simple(page_text)
            
            # Use LLM for advanced extraction
            extracted = await extract_profile_with_llm(page_text, candidate.name, candidate.affiliation)
            
            if extracted:
                # Override with LLM results if available
                if extracted.get('email'):
                    candidate.email = extracted['email']
                if extracted.get('name_cn'):
                    candidate.name_cn = extracted['name_cn']
                if extracted.get('bachelor_univ'):
                    candidate.bachelor_univ = extracted['bachelor_univ']
            
            candidate.verification_time = datetime.now()
            
            logger.info(f"[AuditorNode] Extracted - Email: {candidate.email}, CN: {candidate.name_cn}, Bachelor: {candidate.bachelor_univ}")
    
    return state

