# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Tuple, Optional

from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.colors import white
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, KeepTogether, Paragraph, Table

from .style import get_style_sheet

# -- Classes ------------------------------------------------------------------


class CheckboxList:
    """This class represents a list of checkboxes

    The list starts with a title that should describe the purpose of the
    checkbox list, followed by the checkbox items. At the end a optional list
    of lines will be printed. These lines can be used to add handwritten
    comments.
    """

    def __init__(self, title: str = "Checks", lines: int = 0) -> None:
        """Create a new checkbox list with the given title

        Parameters
        ----------

        title:
            A title that describes the purpose of the checklist

        lines:
            The number of lines for handwritten input that should be added at
            the end of the checklist

        """

        self.title = title
        self.checks: List[Tuple[Checkbox, str]] = []
        self.styles = get_style_sheet()
        self.lines = lines

    def add_checkbox_item(self, text: str, tooltip: str = None) -> None:
        """Add a checkbox item to the checkbox list

        Parameters
        ----------

        text:
            The text that should be added after the checkbox item

        tooltip:
            The tooltip for the checkbox; If you do not specify a tooltip, then
            `text` will also be used for the tooltip.

        """

        self.checks.append((Checkbox(text, tooltip), text))

    def to_flowable(self) -> KeepTogether:
        """Convert the checkbox list into a Flowable

        Returns
        -------

        A Flowable representing this checkbox list

        """

        title = Paragraph(self.title, style=self.styles['Heading3'])

        # Somehow the text columns of a table will contain a lot of
        # trailing whitespace, if some (other) cells contain non-textual
        # data. We work around that by specifying the size of the first
        # column manually.
        checks = Table(self.checks, colWidths=[0.5 * cm, None])

        drawing = Drawing(400, 20)
        drawing.add(Line(6, 0, 350, 0))

        lines = [drawing for _ in range(self.lines)]

        return KeepTogether([title, checks, *lines])


class Checkbox(Flowable):
    """A flowable checkbox"""

    def __init__(self, text: str, tooltip: Optional[str] = None) -> None:
        """Initialize the checkbox using the given arguments

        Parameters
        ----------

        text:
            The name of the checkbox

        tooltip:
            The text displayed in the tooltip of the checkbox; If you do not
            provide a tooltip, then the content of `text` will be used for the
            tooltip too.

        Examples
        --------

        >>> Checkbox(text="A checkbox", tooltip="The tooltip of the box")
        ☑️ A checkbox | Tooltip: The tooltip of the box

        >>> Checkbox(text="Another checkbox")
        ☑️ Another checkbox | Tooltip: Another checkbox

        """

        super().__init__()

        self.text = text
        self.tooltip = text if tooltip is None else tooltip
        self.boxsize = 10

        self.width = self.height = self.boxsize

    def __repr__(self) -> str:
        """The string representation of the checkbox

        Returns
        -------

        A string containing information about the checkbox

        """

        return f"☑️ {self.text} | Tooltip: {self.tooltip}"

    def draw(self) -> None:
        """Draw the checkbox on the canvas"""

        self.canv.saveState()

        form = self.canv.acroForm
        form.checkbox(checked=False,
                      buttonStyle='check',
                      name=self.text,
                      fillColor=white,
                      tooltip=self.tooltip,
                      relative=True,
                      size=self.boxsize)

        self.canv.restoreState()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
