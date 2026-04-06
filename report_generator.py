import io
import csv
from fpdf import FPDF

class ReportGenerator:
    @staticmethod
    def safe_text(text):
        """Clean text for PDF compatibility (Latin-1)."""
        if not text:
            return "-"
        # Replace common Unicode punctuation with ASCII equivalents
        replacements = {
            "—": "-", "–": "-", 
            "’": "'", "‘": "'",
            "“": '"', "”": '"',
            "…": "..."
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        
        # Strip remaining non-Latin1 characters (emojis, etc.)
        try:
            return text.encode("latin-1", "ignore").decode("latin-1").strip()
        except:
            return "Participant"

    @classmethod
    def generate_csv(cls, result):
        """Generate a CSV report with UTF-8 BOM for Excel."""
        output = io.StringIO()
        output.write('\ufeff')  # UTF-8 BOM
        writer = csv.writer(output)
        writer.writerow(["#", "Participant Name", "Email Address", "Status", "Note/Error"])
        
        for i, r in enumerate(result.get("report", []), 1):
            clean_reason = cls.safe_text(r.get("reason", "-"))
            writer.writerow([i, r["name"], r["email"], r.get("status", "unknown"), clean_reason])
            
        return output.getvalue().encode("utf-8")

    @classmethod
    def generate_pdf(cls, result):
        """Generate a professional PDF report."""
        class PDF(FPDF):
            def header(self):
                # Header branding
                self.set_fill_color(124, 111, 255) # SmartCert Accent
                self.rect(0, 0, 210, 35, 'F')
                self.set_text_color(255, 255, 255)
                self.set_font('Helvetica', 'B', 22)
                self.cell(0, 15, 'SmartCert Delivery Report', 0, 1, 'C')
                self.set_font('Helvetica', '', 9)
                subj = cls.safe_text(result.get('subject', 'Certification Batch'))
                self.cell(0, 5, f"Subject: {subj}", 0, 1, 'C')
                self.ln(15)

            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.set_text_color(120, 120, 120)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Summary Section
        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, "1. Executive Summary", 0, 1)
        pdf.set_font('Helvetica', '', 10)
        
        # Stats Table
        pdf.set_fill_color(245, 245, 250)
        pdf.cell(47, 10, f"Total Sent: {result['sent']}", 1, 0, 'C', 1)
        pdf.cell(47, 10, f"Total Failed: {result['failed']}", 1, 0, 'C', 1)
        pdf.cell(47, 10, f"Grand Total: {result['total']}", 1, 0, 'C', 1)
        pct = round((result['sent'] / result['total'] * 100)) if result['total'] > 0 else 0
        pdf.cell(47, 10, f"Success: {pct}%", 1, 1, 'C', 1)
        pdf.ln(8)

        # Details Section
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, "2. Detailed Participant List", 0, 1)
        
        # Table Headers
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(230, 230, 235)
        pdf.set_text_color(60, 60, 60)
        col_width = [10, 45, 55, 25, 55]
        headers = ["#", "Name", "Email", "Status", "Note"]
        
        for i, h in enumerate(headers):
            pdf.cell(col_width[i], 10, h, 1, 0, 'C', 1)
        pdf.ln()

        # Table Rows
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        for i, r in enumerate(result.get('report', []), 1):
            # Row shading
            fill = 1 if i % 2 == 0 else 0
            pdf.set_fill_color(252, 252, 254)
            
            pdf.cell(col_width[0], 9, str(i), 1, 0, 'C', fill)
            pdf.cell(col_width[1], 9, cls.safe_text(r['name'])[:22], 1, 0, 'L', fill)
            pdf.cell(col_width[2], 9, cls.safe_text(r['email'])[:28], 1, 0, 'L', fill)
            
            # Status Color
            if r['status'] == 'sent':
                pdf.set_text_color(30, 120, 30)
            else:
                pdf.set_text_color(180, 40, 40)
            
            pdf.cell(col_width[3], 9, r['status'].upper(), 1, 0, 'C', fill)
            pdf.set_text_color(0, 0, 0)
            
            reason = cls.safe_text(r.get('reason', '-'))[:35]
            pdf.cell(col_width[4], 9, reason, 1, 1, 'L', fill)

        return pdf.output()
