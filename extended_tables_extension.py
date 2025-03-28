from markdown import Markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import tables
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import xml.etree.ElementTree as etree
import re
from typing import Sequence
import markdown

ROW_CLASS_PATTERN = r'\+\.[_\-a-zA-Z][_\-a-zA-Z\d]*'
CELL_CLASS_PATTERN = r'(?<!\+)\.[_\-a-zA-Z][_\-a-zA-Z\d]*'
ROW_HIGHLIGHT_PATTERN = r'\+!\d+'
CELL_HIGHLIGHT_PATTERN = r'(?<!\+)!\d+'
COLSPAN_PATTERN = r'>\d+'
PROPERTIES_PATTERN = (r'^!{ *'
                      f'({ROW_CLASS_PATTERN} *)*' # Group 1
                      f'({CELL_CLASS_PATTERN} *)*' # Group 2
                      f'({ROW_HIGHLIGHT_PATTERN} *)*' # Group 3
                      f'({CELL_HIGHLIGHT_PATTERN} *)*' # Group 4
                      f'({COLSPAN_PATTERN} *)?' # Group 5
                      r'}')

class ExtendedTableProcessor(tables.TableProcessor):
    # I could've figured out a regex that matched the flags in any order
    # However, that sounds like a lot of pain, and I'm not even sure if it would be possible with regex only
    # Add to that the fact that, even using groups, m.group(i) only returns the last match if a group matched multiple times
    # https://docs.python.org/3/library/re.html#re.Match.group
    # So I've just kept them in a fixed order, I don't think anyone would find it too much of an issue
    # (if anyone else apart from me were ever to use this extension, that is)
    # (also, it's definitely possible to have the flags in any order by just using iteration)
    def _build_row(self, row: str, parent: etree.Element, align: Sequence[str | None]) -> None:
        """ Given a row of text, build table cells. """
        tr = etree.SubElement(parent, 'tr')
        tag = 'td'
        if parent.tag == 'thead':
            tag = 'th'
        cells = self._split_row(row)
        # We use align here rather than cells to ensure every row
        # contains the same number of columns.

        i = 0 # We need to be able to increment the index separately due to colspans
        while i < len(align):
            a = align[i] # Get the align value for this column
            c = etree.SubElement(tr, tag) # Create the tr
            try:
                text = cells[i] # Get the text inside the cell WITHOUT stripping
                m = re.match(PROPERTIES_PATTERN, text) # Try to match with the properties at the beginning (right after the pipe)
                if m:
                    if m.group(1) is not None: # If the first group matched, it matched with #.
                        if 'class' not in tr.attrib:
                            tr.attrib['class'] = ''
                        for m2 in re.finditer(ROW_CLASS_PATTERN, text): # Get the highlight number
                            tr.attrib['class'] = f"{tr.attrib['class']} {m2.group(0)[2:]}" # Apply class

                    if m.group(2) is not None: # If the second group matched, it matched with .
                        if 'class' not in c.attrib:
                            c.attrib['class'] = ''
                        for m2 in re.finditer(CELL_CLASS_PATTERN, text):  # Get the highlight number
                            c.attrib['class'] = f"{c.attrib['class']} {m2.group(0)[1:]}"  # Apply class

                    if m.group(3) is not None: # If the third group matched, it matched with #!
                        if 'class' not in tr.attrib:
                            tr.attrib['class'] = ''
                        for m2 in re.finditer(ROW_HIGHLIGHT_PATTERN, text): # Get the highlight number
                            tr.attrib['class'] = f"{tr.attrib['class']} table-highlight-{m2.group(0)[2:]}" # Apply class

                    if m.group(4) is not None: # If the fourth group matched, it matched with !
                        if 'class' not in c.attrib:
                            c.attrib['class'] = ''
                        for m2 in re.finditer(CELL_HIGHLIGHT_PATTERN, text):  # Get the highlight number
                            c.attrib['class'] = f"{c.attrib['class']} table-highlight-{m2.group(0)[1:]}"  # Apply class

                    if m.group(5) is not None: # If the third group matched, it matched with >
                        colspan = re.search(COLSPAN_PATTERN, text).group(0)[1]
                        c.attrib['colspan'] = colspan # Apply colspan
                        i += int(colspan) - 1 # Add colspan-1 to the counter, skipping colspan-1 cells

                c.text = re.sub(PROPERTIES_PATTERN, '', text).strip() # Remove the properties, strip, and set as the text of the cell
            except IndexError:  # pragma: no cover
                c.text = "" # Create an extra empty cell if there aren't enough in the row
            finally:
                i += 1 # Increment counter
            if a:
                if self.config['use_align_attribute']:
                    c.set('align', a)
                else:
                    c.set('style', f'text-align: {a};')

class ExtendedTableExtension(Extension):
    """ Add tables to Markdown, with the following extensions:
    After opening a cell with |, insert !{<options>} to change some attributes of the row or cell
    The available options are:
    +.class    : Apply class the whole row
    .class     : Apply class to the cell
    +!<number> : Apply class table-highlight-<number> to row
    !<number>  : Apply class table-highlight-<number> to cell
    ><number>  : Apply colspan of <number> to cell

    The options must be specified in this order, but multiple values for the same attribute can be applied (except for colspan), and can be separated by spaces
    Example:
        |!{.center-align +!1 >3} text|
    Creates
        <tr class="table-highlight-1">
            ...
            <td class="center-align" colspan="3">text</td>
            ...
        </tr>

    NOTE: when applying a colspan of X, the X cells after it will be discarded (so they may as well be empty)
    Example:
        |!{>4} Span|These|will|be|discarded|but not this one|
    Creates:
        <tr class="table-highlight-1">
            <td colspan="4">Span</td>
            <td>but not this one</td>
        </tr>

    This extensions inherits from TableProcessor/TableExtension, and only modifies the _build_row function
    """

    def __init__(self, **kwargs):
        self.config = {
            'use_align_attribute': [False, 'True to use align attribute instead of style.'],
        }
        """ Default configuration options. """

        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add an instance of `TableProcessor` to `BlockParser`. """
        if '|' not in md.ESCAPED_CHARS:
            md.ESCAPED_CHARS.append('|')
        processor = ExtendedTableProcessor(md.parser, self.getConfigs())
        md.parser.blockprocessors.register(processor, 'extended_table', 75)
