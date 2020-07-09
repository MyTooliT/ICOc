# -- Imports ------------------------------------------------------------------

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

# -- Class --------------------------------------------------------------------


class Report:
    """Generate test reports using ReportLab"""

    def __init__(self):
        """Initialize the report"""

        self.canvas = Canvas('report.pdf', bottomup=0, pagesize=A4)
        self.width, self.height = A4

        self.canvas.setAuthor("MyTooliT")
        self.canvas.setTitle("Test Report")

        self.canvas.drawString(100, 100, "MyTooliT Report")

    def __exit__(self):
        """Store the PDF report"""

        self.canvas.save()
        self.canvas.showPage()
