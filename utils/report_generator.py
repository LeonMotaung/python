import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_report(file):
    # Read the uploaded file
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
    
    # Generate basic analysis
    analysis = {
        'summary': df.describe(),
        'columns': df.columns.tolist(),
        'rows': len(df)
    }
    
    # Generate recommendations
    recommendations = [
        f"Dataset contains {len(df)} rows and {len(df.columns)} columns",
        f"Columns present: {', '.join(df.columns)}",
        "Consider cleaning any missing values" if df.isnull().any().any() else "No missing values found"
    ]
    
    # Create the PDF report
    create_report(analysis, recommendations, os.path.splitext(file.filename)[0])
    
    return {
        'summary': analysis,
        'recommendations': recommendations
    }

def create_report(analysis, recommendations, filename):
    report_path = f'reports/{filename}_report.pdf'
    os.makedirs('reports', exist_ok=True)
    
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("Data Analysis Report", styles['Title']))
    
    elements.append(Paragraph("Summary Statistics:", styles['Heading2']))
    elements.append(Paragraph(str(analysis['summary']), styles['BodyText']))
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Recommendations:", styles['Heading2']))
    for rec in recommendations:
        elements.append(Paragraph(rec, styles['BodyText']))
        
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Visualizations:", styles['Heading2']))
    for plot in os.listdir('static/plots'):
        img = Image(f'static/plots/{plot}', width=400, height=300)
        elements.append(img)
    
    doc.build(elements)
    return report_path