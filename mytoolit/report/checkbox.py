# -- Imports ------------------------------------------------------------------

from typing import Optional

from reportlab.lib.colors import white
from reportlab.platypus import Flowable

# -- Class --------------------------------------------------------------------


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
