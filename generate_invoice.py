from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # Logo
        img_path = r"C:\Users\PRO\.gemini\antigravity\brain\1902c0c9-f63d-44e4-9678-56f1b16d3d99\.user_uploaded\media_1787930142817.png"
        self.image(img_path, x=10, y=8, w=50)
        
        # Title
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'INVOICE', new_x="LMARGIN", new_y="NEXT", align='R')
        self.set_font('helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Date: ' + datetime.now().strftime("%B %d, %Y"), new_x="LMARGIN", new_y="NEXT", align='R')
        self.cell(0, 5, 'Invoice No: INV-20260828', new_x="LMARGIN", new_y="NEXT", align='R')
        
        # Add some space after the logo and title
        self.ln(25)

    def footer(self):
        self.set_y(-30)
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(128)
        self.cell(0, 5, 'Digitally Signed by:', new_x="LMARGIN", new_y="NEXT", align='R')
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, 'Ananthajith KS', new_x="LMARGIN", new_y="NEXT", align='R')
        self.set_font('helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Technical Director', new_x="LMARGIN", new_y="NEXT", align='R')
        
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Thank you for your business.', align='C')

# Create PDF
pdf = PDF()
pdf.add_page()

# Invoice Info
pdf.set_font('helvetica', 'B', 12)
pdf.cell(100, 6, 'Project Details:', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('helvetica', '', 11)
pdf.cell(100, 6, 'Project: VectorPredict EWS Platform', new_x="LMARGIN", new_y="NEXT")
pdf.cell(100, 6, 'Client: Teena', new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)

# Table Header
pdf.set_font('helvetica', 'B', 11)
pdf.set_fill_color(240, 240, 240)
pdf.cell(130, 10, ' Description of Services', border=1, new_x="RIGHT", new_y="TOP", align='L', fill=True)
pdf.cell(60, 10, ' Amount (INR) ', border=1, new_x="LMARGIN", new_y="NEXT", align='R', fill=True)

# Table Content
pdf.set_font('helvetica', '', 11)
pdf.cell(130, 12, ' VectorPredict ML Architecture & Data Pipeline', border='LR', new_x="RIGHT", new_y="TOP", align='L')
pdf.cell(60, 12, ' 5,399.00 ', border='LR', new_x="LMARGIN", new_y="NEXT", align='R')

# Empty row for spacing
pdf.cell(130, 20, '', border='LR', new_x="RIGHT", new_y="TOP")
pdf.cell(60, 20, '', border='LR', new_x="LMARGIN", new_y="NEXT")

# Subtotal
pdf.set_font('helvetica', 'B', 11)
pdf.cell(130, 10, ' Subtotal:', border='L', new_x="RIGHT", new_y="TOP", align='R')
pdf.set_font('helvetica', '', 11)
pdf.cell(60, 10, ' 5,399.00 ', border='R', new_x="LMARGIN", new_y="NEXT", align='R')

# Discount
pdf.set_font('helvetica', 'B', 11)
pdf.set_text_color(220, 38, 38) # Red
pdf.cell(130, 10, ' Discount:', border='L', new_x="RIGHT", new_y="TOP", align='R')
pdf.set_font('helvetica', '', 11)
pdf.cell(60, 10, ' - 400.00 ', border='R', new_x="LMARGIN", new_y="NEXT", align='R')

# Total
pdf.set_text_color(0, 0, 0)
pdf.set_fill_color(24, 75, 137) # Blue from the logo
pdf.set_text_color(255, 255, 255)
pdf.set_font('helvetica', 'B', 12)
pdf.cell(130, 12, ' TOTAL PAYABLE (INR):', border=1, new_x="RIGHT", new_y="TOP", align='R', fill=True)
pdf.cell(60, 12, ' Rs 4,999.00 ', border=1, new_x="LMARGIN", new_y="NEXT", align='R', fill=True)

pdf.output('VectorPredict_Invoice.pdf')
