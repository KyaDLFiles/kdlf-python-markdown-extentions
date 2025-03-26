
_RE_HEADERS = r'#+(?= )'

class AddBlanksAroundHeadersPreprocessor(Preprocessor):
    """ Add a blank line before and after all headers if not already present
    This is needed because all headers must be alone in their own block for SectionsViaHeaders to work"""
    def run(self, lines):
        new_lines = [] # Lines are handled in a separate lists because it would be a pain to have a list that mutates while iterating on it
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
        md.preprocessors.register(AddBlanksAroundHeadersPreprocessor(md), 'blanks', 175)

class SectionsViaHeadersBlockProcessor(BlockProcessor):
    """Wraps sections of the document delimited by headers of different level in <section> tags,
    and applies an id derived from the header text to it"""
    # Holy JESUS did this take long to figure out


    def test(self, parent, block):
        return re.match(_RE_HEADERS, block)

    def run(self, parent, blocks):
        def _wrap(wrap_end: int) -> None:
            # Create a new <section> to wrap the block around
            e = etree.SubElement(parent, 'section')
            # Add the HTML header as it's first child, and set its text
            child = etree.SubElement(e, f'h{starting_level}')
            child.text = header_text
            e.set('style', 'border: 1px solid red;')
            e.set('id', section_id)
            # Iteratively call the parser on the blocks BETWEEN the two found headers (or end of block/file)
            # The header was added manually above because otherwise it would've been discarded since here it's being skipped
            self.parser.parseBlocks(e, blocks[1:wrap_end])
            # Remove used blocks
            for i in range(0, wrap_end):
                blocks.pop(0)

        # First of all, get the starting block, what has matched (the #s), and how many of them there are
        starting_block = blocks[0]
        starting_match = re.match(_RE_HEADERS, starting_block).group()
        starting_level = len(starting_match) # Number of #s in the header
        header_text = starting_block[starting_level + 1:] # Get the actual text in the header
        section_id = re.sub(r' +', '-', header_text.lower().strip()) # Lowercase, strip, and replace spaces with hyphens

        end_matched = False
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
    """ Extention to wrap sections of the document delimited by headers of different level in <section> tags,
    and apply an id derived from the header text to it

    For example:
    # Section 1
        # Subsection 1A
            foo
        # Subsection 1B
            bar
    # Section 2
        foobar

    Becomes:
    <section id='section-1'>
        <section id='section-1a'>
            foo
        </section>
        <section id='section-1b'>
            bar
        </section>
    </section>
    <section id='section-2'>
        foobar
    </section>"""
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(SectionsViaHeadersBlockProcessor(md.parser), 'box', 175)
