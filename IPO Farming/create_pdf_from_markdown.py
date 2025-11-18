"""
Create PDF directly from markdown using reportlab
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import re

def create_pdf_from_markdown(md_file_path, pdf_file_path):
    """
    Create a formatted PDF from markdown content
    """
    # Read markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    story = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1a1a1a',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor='#34495e',
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=11,
        textColor='#34495e',
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#333333',
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#333333',
        spaceAfter=4,
        leftIndent=20,
        bulletIndent=10,
        fontName='Helvetica'
    )

    # Parse content
    lines = content.split('\n')
    i = 0
    first_heading = True

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip multiple empty lines
        if not line:
            if len(story) > 0:
                story.append(Spacer(1, 0.1*inch))
            i += 1
            continue

        # Main title (# )
        if line.startswith('# ') and not line.startswith('## '):
            text = line[2:].strip()
            if first_heading:
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 0.3*inch))
                first_heading = False
            else:
                story.append(Paragraph(text, heading1_style))
                story.append(Spacer(1, 0.2*inch))

        # Heading 2 (## )
        elif line.startswith('## ') and not line.startswith('### '):
            text = line[3:].strip()
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(text, heading1_style))

        # Heading 3 (### )
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(text, heading2_style))

        # Horizontal rule (---)
        elif line.strip() == '---':
            story.append(Spacer(1, 0.2*inch))

        # Bullet points (- )
        elif line.startswith('- '):
            text = line[2:].strip()
            # Convert markdown bold to HTML
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(f"• {text}", bullet_style))

        # Numbered lists (1. , 2. , etc.)
        elif re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s', '', line).strip()
            # Convert markdown bold to HTML
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            match = re.match(r'^(\d+)\.', line)
            number = match.group(1) if match else '1'
            story.append(Paragraph(f"{number}. {text}", bullet_style))

        # Regular paragraph
        else:
            # Convert markdown bold to HTML
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(text, body_style))

        i += 1

    # Build PDF
    doc.build(story)
    print(f"PDF created successfully: {pdf_file_path}")

if __name__ == "__main__":
    import os

    # File paths
    base_dir = "/Users/akbarpathan/Desktop/Dev/Trading Expirements/IPO Farming"
    md_file = os.path.join(base_dir, "IPO_Backtest_Plan.md")
    pdf_file = os.path.join(base_dir, "IPO_Backtest_Plan.pdf")

    print("Creating PDF from markdown...")
    create_pdf_from_markdown(md_file, pdf_file)
    print("\nDone! Files created:")
    print(f"- Word: {base_dir}/IPO_Backtest_Plan.docx")
    print(f"- PDF: {pdf_file}")
