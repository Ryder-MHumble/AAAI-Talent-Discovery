"""Excel Export Service"""

import pandas as pd
from typing import List
from io import BytesIO
import logging

from app.api.models import CandidateProfile

logger = logging.getLogger(__name__)


def generate_excel_report(candidates: List[CandidateProfile], job_id: str) -> BytesIO:
    """
    Generate an Excel file from candidate results.
    
    Args:
        candidates: List of CandidateProfile objects
        job_id: Job identifier
        
    Returns:
        BytesIO buffer containing the Excel file
    """
    # Filter to only include verified candidates
    verified = [c for c in candidates if c.status == "VERIFIED"]
    
    logger.info(f"[ExcelService] Generating report for {len(verified)} verified candidates")
    
    # Prepare data for DataFrame
    data = []
    for candidate in verified:
        data.append({
            "Name": candidate.name,
            "Chinese Name": candidate.name_cn or "N/A",
            "Current Affiliation": candidate.affiliation,
            "Role": candidate.role,
            "Homepage": candidate.homepage or "N/A",
            "Email": candidate.email or "N/A",
            "Bachelor University": candidate.bachelor_univ or "N/A",
            "Verification Time": candidate.verification_time.strftime("%Y-%m-%d %H:%M:%S") if candidate.verification_time else "N/A"
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Verified Scholars', index=False)
        
        # Also add a summary sheet
        summary_data = {
            "Metric": [
                "Job ID",
                "Total Candidates",
                "Verified",
                "Failed",
                "Skipped",
                "Generated At"
            ],
            "Value": [
                job_id,
                len(candidates),
                len([c for c in candidates if c.status == "VERIFIED"]),
                len([c for c in candidates if c.status == "FAILED"]),
                len([c for c in candidates if c.status == "SKIPPED"]),
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    buffer.seek(0)
    
    logger.info(f"[ExcelService] Excel report generated successfully")
    
    return buffer


def generate_full_report(candidates: List[CandidateProfile], job_id: str) -> BytesIO:
    """
    Generate a comprehensive Excel file with all candidates (all statuses).
    
    Args:
        candidates: List of CandidateProfile objects
        job_id: Job identifier
        
    Returns:
        BytesIO buffer containing the Excel file
    """
    logger.info(f"[ExcelService] Generating full report for {len(candidates)} candidates")
    
    # Prepare data for DataFrame
    data = []
    for candidate in candidates:
        data.append({
            "Name": candidate.name,
            "Chinese Name": candidate.name_cn or "",
            "Affiliation": candidate.affiliation,
            "Role": candidate.role,
            "Status": candidate.status,
            "Homepage": candidate.homepage or "",
            "Email": candidate.email or "",
            "Bachelor University": candidate.bachelor_univ or "",
            "Skip Reason": candidate.skip_reason or "",
            "Verification Time": candidate.verification_time.strftime("%Y-%m-%d %H:%M:%S") if candidate.verification_time else ""
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Candidates', index=False)
    
    buffer.seek(0)
    
    return buffer

