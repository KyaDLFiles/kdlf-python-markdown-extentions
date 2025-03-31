from markdown.extensions import tables
from markdown.extensions import Extension
from typing import Sequence
import xml.etree.ElementTree as etree
import re
import copy

ROWSPAN_DICT_DEFAULT = {"rowspan": 1, "colspan": 1}

ROW_CLASS_PATTERN = r'\+\.[_\-a-zA-Z][_\-a-zA-Z\d]*'
CELL_CLASS_PATTERN = r'(?<!\+)\.[_\-a-zA-Z][_\-a-zA-Z\d]*'
ROW_HIGHLIGHT_PATTERN = r'\+!\d+'
CELL_HIGHLIGHT_PATTERN = r'(?<!\+)!\d+'
COLSPAN_PATTERN = r'\>\d+'
ROWSPAN_PATTERN = r'\^\d+'
PROPERTIES_PATTERN = (r'^!{ *'
                      f'({ROW_CLASS_PATTERN} *)*' # Group 1
                      f'({CELL_CLASS_PATTERN} *)*' # Group 2
                      f'({ROW_HIGHLIGHT_PATTERN} *)*' # Group 3
                      f'({CELL_HIGHLIGHT_PATTERN} *)*' # Group 4
                      f'({COLSPAN_PATTERN} *)?' # Group 5
                      f'({ROWSPAN_PATTERN} *)?' # Group 6
                      r'}')

class ExtendedTableProcessor(tables.TableProcessor):
    # I could've figured out a regex that matched the flags in any order
    # However, that sounds like a lot of pain, and I'm not even sure if it would be possible with regex only
    # Add to that the fact that, even using groups, m.group(i) only returns the last match if a group matched multiple times
    # https://docs.python.org/3/library/re.html#re.Match.group
    # So I've just kept them in a fixed order, I don't think anyone would find it too much of an issue
    # (if anyone else apart from me were ever to use this extension, that is)
    # (also, it's definitely possible to have the flags in any order by just using iteration)
    def run(self, parent: etree.Element, blocks: list[str]):
        # Unfortunately I had to copy the whole function because I can't intercept len(align) otherwise
        """ Parse a table block and build table. """
        block = blocks.pop(0).split('\n')
        header = block[0].strip(' ')
        rows = [] if len(block) < 3 else block[2:]

        # Get alignment of columns
        align: list[str | None] = []
        for c in self.separator:
            c = c.strip(' ')
            if c.startswith(':') and c.endswith(':'):
                align.append('center')
            elif c.startswith(':'):
                align.append('left')
            elif c.endswith(':'):
                align.append('right')
            else:
                align.append(None)

        # Initialize rowspans
        self.rowspans = []
        for k in range(len(align)):
            self.rowspans.append(copy.deepcopy(ROWSPAN_DICT_DEFAULT))

        # Build table
        table = etree.SubElement(parent, 'table')
        thead = etree.SubElement(table, 'thead')
        self._build_row(header, thead, align)
        tbody = etree.SubElement(table, 'tbody')
        if len(rows) == 0:
            # Handle empty table
            self._build_empty_row(tbody, align)
        else:
            for row in rows:
                self._build_row(row.strip(' '), tbody, align)

    def _build_row(self, row: str, parent: etree.Element, align: Sequence[str | None]) -> None:
        """ Given a row of text, build table cells. """
        tr = etree.SubElement(parent, 'tr')
        tag = 'td'
        if parent.tag == 'thead':
            tag = 'th'
        cells = self._split_row(row)
        # We use align here rather than cells to ensure every row
        # contains the same number of columns.

        i = 0 # "actual" index of the cell (if you consider colspanned cells as separate)
        j = 0 # index of cell as being read from the file
        while i < len(align):
            if self.rowspans[i]["rowspan"] < 2:
                a = align[i] # Get the align value for this column
                c = etree.SubElement(tr, tag) # Create the td
                colspan = 1
                rowspan = 1
                try:
                    text = cells[j] # Get the text inside the cell WITHOUT stripping
                    m = re.match(PROPERTIES_PATTERN, text) # Try to match with the properties at the beginning (right after the pipe)
                    if m:
                        if m.group(1) is not None: # If the first group matched, it matched with +.
                            if 'class' not in tr.attrib:
                                tr.attrib['class'] = ''
                            for m2 in re.finditer(ROW_CLASS_PATTERN, text): # Get the highlight number
                                tr.attrib['class'] = f"{tr.attrib['class']} {m2.group(0)[2:]}" # Apply class

                        if m.group(2) is not None: # If the second group matched, it matched with .
                            if 'class' not in c.attrib:
                                c.attrib['class'] = ''
                            for m2 in re.finditer(CELL_CLASS_PATTERN, text):  # Get the highlight number
                                c.attrib['class'] = f"{c.attrib['class']} {m2.group(0)[1:]}"  # Apply class

                        if m.group(3) is not None: # If the third group matched, it matched with +!
                            if 'class' not in tr.attrib:
                                tr.attrib['class'] = ''
                            for m2 in re.finditer(ROW_HIGHLIGHT_PATTERN, text): # Get the highlight number
                                tr.attrib['class'] = f"{tr.attrib['class']} table-highlight-{m2.group(0)[2:]}" # Apply class

                        if m.group(4) is not None: # If the fourth group matched, it matched with !
                            if 'class' not in c.attrib:
                                c.attrib['class'] = ''
                            for m2 in re.finditer(CELL_HIGHLIGHT_PATTERN, text):  # Get the highlight number
                                c.attrib['class'] = f"{c.attrib['class']} table-highlight-{m2.group(0)[1:]}"  # Apply class

                        if m.group(5) is not None: # If the fifth group matched, it matched with >
                            colspan = int(re.search(COLSPAN_PATTERN, text).group(0)[1])
                            c.attrib['colspan'] = str(colspan) # Apply colspan

                        if m.group(6) is not None: # If the sixth group matched, it matched with ^
                            rowspan = int(re.search(ROWSPAN_PATTERN, text).group(0)[1])
                            c.attrib['rowspan'] = str(rowspan)


                        self.rowspans[i]["rowspan"] = rowspan # Set the rowspan for this cell
                        self.rowspans[i]["colspan"] = colspan # Set the colspan for this cell
                        if colspan > 1: # Skip n-1 cells if cell has n colspan
                            i += colspan - 1

                    c.text = re.sub(PROPERTIES_PATTERN, '', text).strip() # Remove the properties, strip, and set as the text of the cell
                except IndexError:  # pragma: no cover
                    c.text = "" # Create an extra empty cell if there aren't enough in the row
                finally:
                    j += 1
                if a:
                    if self.config['use_align_attribute']:
                        c.set('align', a)
                    else:
                        c.set('style', f'text-align: {a};')
            else: # if there's a cell in a previous row that has a rowspan overriding this cell, don't generate anything and decrement the counter
                k = i
                j += 1 # Skip dummy cell in markdown
                if self.rowspans[k]["colspan"] != 0:
                    i += self.rowspans[k]["colspan"] - 1 # Skip extra cells if rowspanned column also has rowspan
                self.rowspans[k]["rowspan"] -= 1 # Decrease remaining

            i += 1

class ExtendedTableExtension(Extension):
    """ Add tables to Markdown, with the following extensions:
    After opening a cell with |, insert !{<options>} to change some attributes of the row or cell
    The available options are:
    +.class    : Apply class the whole row
    .class     : Apply class to the cell
    +!<number> : Apply class table-highlight-<number> to row
    !<number>  : Apply class table-highlight-<number> to cell
    ><number>  : Apply colspan of <number> to cell
    ^<number>  : Apply rowspan of <number> to cell

    The options must be specified in this order, but multiple values for the same attribute can be applied (except for colspan), and can be separated by spaces
    Example:
        |!{.center-align +!1 >3} text|
    Creates
        <tr class="table-highlight-1">
            ...
            <td class="center-align" colspan="3">text</td>
            ...
        </tr>

    NOTE: when applying a rowspan of X, the X cells below that cell will be discarded (so they may as well be empty)
    Example:
        |!{^5} Span   |A|
        |These        |B|
        |Will         |C|
        |Be           |D|
        |Discared     |E|
        |But not this |F|
    Creates:
        <tr>
            <td rowspan="5">Span</td>
            <td>A</td>
        </tr>
        <tr>
            <td>B</td>
        </tr>
        <tr>
            <td>C</td>
        </tr>
        <tr>
            <td>D</td>
        </tr>
        <tr>
            <td>E</td>
        </tr>
        <tr>
            <td>But not this</td>
            <td>E</td>
        </tr>

    The same will NOT happen with colspan
    Example:
        |!{>3}Span|After span|
        |A|B|C    |D         |
    Creates:
        <tr>
            <td colspan="3">Span</td>
            <td>After span</td>
        </tr>
        <tr>
            <td>A</td>
            <td>B</td>
            <td>C</td>
            <td>D</td>
        </tr>

    IMPORTANT: malformed tables (eg: having cells with a colspan and rowspan that are overlapping) will generate unexpected results

    This extensions inherits from TableProcessor/TableExtension, and only modifies the _build_row and run() functions
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
