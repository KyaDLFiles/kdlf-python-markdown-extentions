from markdown import Markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import xml.etree.ElementTree as etree
import re
import markdown

_RE_HEADERS = re.compile(r'#+(?= )', re.UNICODE | re.DOTALL)

class AddBlanksAroundHeadersPreprocessor(Preprocessor):
    """ Add a blank line before and after all headers if not already present
    This is needed because all headers must be alone in their own block for SectionsViaHeaders to work"""
    def run(self, lines):
        new_lines = [] # Lines are stored in a separate lists because it would be a pain to have a list that mutates while iterating on it
        for line_num, line in enumerate(lines):
            if re.search(_RE_HEADERS, line): # Check if current line is a header
                # Check previous and next line, and add blanks if needed
                if lines[line_num - 1] != '':
                    new_lines.append('')
                new_lines.append(line)
                if lines[line_num + 1] != '':
                    new_lines.append('')
            else:
                new_lines.append(line)
        return new_lines


class AddBlanksAroundHeadersExtension(Extension):
    """Extension to add blank lines before and after headers, ensuring each is in its own block"""
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        md.preprocessors.register(AddBlanksAroundHeadersPreprocessor(md), 'header-blanks', 200)

class SectionsViaHeadersBlockProcessor(BlockProcessor):
    """Wraps sections of the document delimited by headers of different level in <section> tags"""

    def test(self, parent, block):
        return re.match(_RE_HEADERS, block)

    def run(self, parent, blocks):
        def _wrap(wrap_end: int) -> None:
            # Create a new <section> to wrap the block around
            e = etree.SubElement(parent, 'section')
            # Add the HTML header as it's first child, and set its text
            child = etree.SubElement(e, f'h{starting_level}')
            child.text = header_text
            e.attrib["class"] = f"section-level-{starting_level}"
            # Iteratively call the parser on the blocks BETWEEN the two found headers (or end of block/file) (excluding the header that initiated the match)
            self.parser.parseBlocks(e, blocks[1:wrap_end])
            # Remove used blocks
            for i in range(0, wrap_end):
                blocks.pop(0)

        # First of all, get the starting block, what has matched (the #s), and how many of them there are
        starting_block = blocks[0]
        starting_match = re.match(_RE_HEADERS, starting_block).group()
        starting_level = len(starting_match) # Number of #s in the header
        header_text = starting_block[starting_level + 1:] # Get the actual text in the header

        # Find next block with the same level of heading
        for block_num, block in enumerate(blocks):
            if block_num == 0:
                # Skip the block that initiated the search
                continue
            result = re.search(_RE_HEADERS, block)
            if result:
                # If another header is found, check if it's the same level of heading
                ending_match = result.group()
                ending_level = len(ending_match)
                if starting_level == ending_level:
                    # If it is, wrap everything up until it in a section
                    _wrap(block_num)
                    return True

        # If no other header is found, the block/file has ended, so wrap what's been found so far in a section
        # Since no ending header exists, add 1 to the number the for loop ended on to include the last block before the end in the section
        _wrap(block_num + 1)
        return True


class SectionsViaHeadersExtension(Extension):
    """ Extention to wrap sections of the document delimited by headers of different level in <section> tags

    For example:
    # Section 1
        # Subsection 1A
            foo
        # Subsection 1B
            bar
    # Section 2
        foobar

    Becomes:
    <section>
        <h1>Section 1</h1>
        <section>
            <h2>Section 1A</h2>
            foo
        </section>
        <section>
            <h2>Section 1B</h2>
            bar
        </section>
    </section>
    <section>
        <h1>Section 2</h1>
        foobar
    </section>"""
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        md.parser.blockprocessors.register(SectionsViaHeadersBlockProcessor(md.parser), 'header-sections', 201)
