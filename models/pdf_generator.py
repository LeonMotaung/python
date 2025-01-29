from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

def generate_pdf(filename, df, summary_stats, image_paths):
    # Get the absolute path for the PDF file
    base_dir = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    pdf_path = os.path.join(upload_dir, filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Data Analysis Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Add summary statistics table
    stats_data = [['Metric', 'Value']]
    for key, value in summary_stats.items():
        stats_data.append([key, str(value)])
    
    stats_table = Table(stats_data, colWidths=[300, 200])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Add visualizations (4 per page)
    elements.append(Paragraph("Visualizations", styles['Heading1']))
    elements.append(Spacer(1, 20))
    
    # Calculate image size to fit 4 per page
    max_width = 350
    max_height = 250
    
    # Group images into rows of 2
    for i in range(0, len(image_paths), 2):
        images_row = []
        for j in range(2):
            if i + j < len(image_paths):
                # Convert relative URL to absolute file path
                img_url = image_paths[i + j]
                img_path = os.path.join(base_dir, 'static', img_url.split('/static/')[-1])
                
                try:
                    img = Image(img_path, width=max_width, height=max_height)
                    images_row.append(img)
                except Exception as e:
                    print(f"Error processing image: {e}")
                    continue
        
        if images_row:
            # Create a table for the row of images
            image_table = Table([images_row], colWidths=[max_width] * len(images_row))
            image_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(image_table)
            elements.append(Spacer(1, 20))
    
    # Build the PDF
    doc.build(elements)
    return pdf_path
