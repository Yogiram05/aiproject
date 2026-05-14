"""
PDF Generator - Creates redacted PDFs and claim summaries
"""

from pathlib import Path
from typing import Union
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime


def generate_redacted_pdf(
    original_text: str,
    redacted_text: str,
    output_path: Union[str, Path]
):
    """Generate PDF with redacted content"""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a')
    )
    story.append(Paragraph("Redacted Medical Document", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Timestamp
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Redacted content
    story.append(Paragraph("<b>Redacted Content:</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    
    for line in redacted_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['Normal']))
    
    doc.build(story)


def generate_claim_summary_pdf(
    claim_data: dict,
    output_path: Union[str, Path]
):
    """Generate claim summary PDF"""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Insurance Claim Summary", styles['Title']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Claim details
    story.append(Paragraph(f"Claim ID: {claim_data.get('claim_id', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Decision
    decision = claim_data.get('decision', 'Unknown')
    story.append(Paragraph(f"<b>Decision:</b> {decision.upper()}", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))
    
    doc.build(story)
