"""Support code to add PDF images to PDF (test reports)

Original Source: https://stackoverflow.com/questions/31712386
"""

# -- Imports ------------------------------------------------------------------

from pdfrw import PdfReader, PdfDict
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.platypus import Flowable

# -- Class --------------------------------------------------------------------


class PDFImage(Flowable):
    """Create a flowable object from a PDF"""

    def __init__(self, filepath, width=200, height=200):
        """Initialize the flowable

        Parameters
        ----------

        filepath:
            A path to the PDF object this object represents
        width:
            The width of the PDF object
        height:
            The height of the PDF object
        """

        super().__init__()

        self.width = width
        self.height = height

        with open(filepath, "rb") as pdf_data:
            (page,) = PdfReader(pdf_data).pages
            self.data = pagexobj(page)

    # pylint: disable=unused-argument

    def wrap(self, availWidth, availHeight):
        """Wrap the PDF object according to the given dimensions

        Parameters
        ----------

        availWidth:
            The width of the wrapped PDF object
        availHeight:
            The height of the wrapped PDF object

        Returns
        -------

        The dimensions of the wrapped object
        """
        return self.width, self.height

    # pylint: enable=unused-argument

    def drawOn(self, canvas, x, y, _=0):
        """Draw the PDF object on the given canvas

        Parameters
        ----------

        canvas:
            The canvas where the flowable should be placed
        x:
            The x position of the PDF inside the canvas
        y:
            The y position of the PDF inside the canvas
        _:
            Ignored parameter that stores offset data for the alignment
        """

        canvas.saveState()

        data = self.data
        if isinstance(data, PdfDict):
            x_scale = self.width / data.BBox[2]
            y_scale = self.height / data.BBox[3]
            canvas.translate(x, y)
            canvas.scale(x_scale, y_scale)
            canvas.doForm(makerl(canvas, data))
        else:
            canvas.drawImage(
                self.img_data,  # pylint: disable=no-member
                x,
                y,
                self.width,
                self.height,
            )

        canvas.restoreState()
