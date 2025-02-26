"""Support for adding forms (such as a checkbox) to PDF documents"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Tuple, Optional

from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.lib.colors import white
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, KeepTogether, Paragraph, Table

from icotronic.report.style import get_style_sheet

# -- Classes ------------------------------------------------------------------

# pylint: disable=too-few-public-methods


class Signature:
    """This class represents a form for adding a signature"""

    def __init__(self) -> None:
        """Create a new signature"""

        self.signature = Drawing(400, 30)

        style = get_style_sheet()["Normal"]

        indent = 180
        line_start = indent + 50
        line_end = line_start + 150
        self.signature.add(
            String(
                indent,
                0,
                "Signature:",
                fontName=style.fontName,
                fontSize=style.fontSize,
            )
        )
        self.signature.add(Line(line_start, 0, line_end, 0))

    def to_flowable(self) -> Drawing:
        """Convert the signature list into a Flowable

        Returns
        -------

        A Flowable representing this signature

        """

        return self.signature


# pylint: enable=too-few-public-methods


class CheckBoxList:
    """This class represents a list of checkboxes

    The list starts with a title that should describe the purpose of the
    checkbox list, followed by the checkbox items. At the end a optional list
    of text fields will be added. These text fields can be used to add
    additional comments.
    """

    def __init__(self, title: str = "Checks", text_fields: int = 0) -> None:
        """Create a new checkbox list with the given title

        Parameters
        ----------

        title:
            A title that describes the purpose of the checklist

        text_fields:
            The number of text fields for additional comments that should be
            added at the end of the checklist.

        """

        self.title = title
        self.checks: List[Tuple[CheckBox, str]] = []
        self.styles = get_style_sheet()
        self.text_fields = text_fields

    def add_checkbox_item(
        self, text: str, tooltip: Optional[str] = None
    ) -> None:
        """Add a checkbox item to the checkbox list

        Parameters
        ----------

        text:
            The text that should be added after the checkbox item

        tooltip:
            The tooltip for the checkbox; If you do not specify a tooltip, then
            `text` will also be used for the tooltip.

        """

        tooltip = text if tooltip is None else tooltip
        self.checks.append((CheckBox(tooltip), text))

    def to_flowable(self) -> KeepTogether:
        """Convert the checkbox list into a Flowable

        Returns
        -------

        A Flowable representing this checkbox list

        """

        title = Paragraph(self.title, style=self.styles["Heading3"])

        # Somehow the text columns of a table will contain a lot of
        # trailing whitespace, if some (other) cells contain non-textual
        # data. We work around that by specifying the size of the first
        # column manually.
        checks = Table(self.checks, colWidths=[0.5 * cm, None])

        text_fields = [
            TextField("Additional comments") for _ in range(self.text_fields)
        ]

        return KeepTogether([title, checks, *text_fields])


class CheckBox(Flowable):
    """A flowable checkbox"""

    def __init__(self, tooltip: Optional[str] = None) -> None:
        """Initialize the checkbox using the given arguments

        Parameters
        ----------

        tooltip:
            The text displayed in the tooltip of the checkbox

        Examples
        --------

        >>> CheckBox(tooltip="The tooltip of the box")
        ☑️ Tooltip: The tooltip of the box

        >>> CheckBox()
        ☑️

        """

        super().__init__()

        self.tooltip = tooltip
        self.boxsize = 10

        self.width = self.height = self.boxsize

    def __repr__(self) -> str:
        """The string representation of the checkbox

        Returns
        -------

        A string containing information about the checkbox

        """

        text = f" Tooltip: {self.tooltip}" if self.tooltip is not None else ""
        return f"☑️{text}"

    def draw(self) -> None:
        """Draw the checkbox on the canvas"""

        self.canv.saveState()

        form = self.canv.acroForm
        form.checkbox(
            checked=False,
            buttonStyle="check",
            fillColor=white,
            tooltip=self.tooltip,
            relative=True,
            size=self.boxsize,
        )

        self.canv.restoreState()


class TextField(Flowable):
    """A flowable text box"""

    def __init__(self, tooltip: Optional[str] = None) -> None:
        """Initialize the text box using the given arguments

        Parameters
        ----------

        tooltip:
            The text displayed in the tooltip of the text

        Example
        -------

        >>> TextField(tooltip="The tooltip of the text field")
        📝 Tooltip: The tooltip of the text field

        """

        super().__init__()

        self.tooltip = tooltip

        self.indent = 6  # Indent slightly to match indentation of checkboxes
        self.width = 350
        self.height = 18
        self.styles = get_style_sheet()

    def __repr__(self) -> str:
        """The string representation of the checkbox

        Returns
        -------

        A string containing information about the checkbox

        """

        text = f" Tooltip: {self.tooltip}" if self.tooltip is not None else ""
        return f"📝{text}"

    def draw(self) -> None:
        """Draw the text box on the canvas"""

        self.canv.saveState()

        form = self.canv.acroForm
        style = self.styles["Normal"]
        form.textfield(
            x=self.indent,
            fontName=style.fontName,
            fontSize=style.fontSize,
            fillColor=white,
            tooltip=self.tooltip,
            relative=True,
            borderWidth=0.5,
            width=self.width,
            height=self.height,
        )

        self.canv.restoreState()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
