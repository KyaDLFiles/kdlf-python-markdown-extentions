from markdown import Markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import xml.etree.ElementTree as etree
import re
import markdown

class PS2ButtonsExtension(Extension):
    """Extension to quickly insert images of PS2 buttons inline
    Buttons are abbreviated as:
    q (sQuare), x (cross), o (circle), t (Triangle), du, dl, dd, dr (Dpad Up, Left, Down, Right), l1, l2, l3, r1, r2, r3, st (STart), se (SElect)
    @!<abbreviation> replaces with the image of the button only, @!!<abbreviation> replaces with the image and name of the button as text
    To make things easier, the filenames (apart from the extension) of the image files must be the same as the abbreviations

    Takes two config options:
    'imgs_path' (default: '') indicates the path to the directory containing the image files
    'imgs_extension' (default: '.png') indicates the extension of the image files (without the dot)

    Example:
    @!s → <span class='inline-button'><img ...></span>
    @!!s→ <span class='inline-button'><img ...>&nbsp;Square</span>"""
    def extendMarkdown(self, md):
        PS2_BUTTONS_PATTERN = r'(@!{1,2})(t|q|x|o|du|dl|dd|dr|l1|l2|l3|r1|r2|r3|st|se)'

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(PS2ButtonsProcessor(PS2_BUTTONS_PATTERN, md, self), "ps2_buttons", 175)

    def __init__(self, **kwargs):
        self.config = {
            #TODO: idk what the first item in the list does
            "imgs_path": ["", "Path to the image files"],
            "imgs_extension": [".png", "Extension of the image files"]
        }
        super(PS2ButtonsExtension, self).__init__(**kwargs)


class PS2ButtonsProcessor(InlineProcessor):
    BUTTON_NAMES = {
        'q': "Square",
        'x': "Cross",
        'o': "Circle",
        't': "Triangle",
        'st': "Start",
        'se': "Select",
        'l1': "L1",
        'l2': "L2",
        'l3': "L3",
        'r1': "R1",
        'r2': "R2",
        'r3': "R3",
        'du': "Dpad up",
        'dl': "Dpad left",
        'dd': "Dpad down",
        'dr': "Dpad right"
    }
    SPAN_CLASS = "inline-btn"

    # The extension needs to be passed to read the config (I'm not sure if it's the best thing to do, but I'm pretty sure I saw an official extension doing it)
    def __init__(self, pattern: str, md: Markdown, ext: PS2ButtonsExtension):
        super().__init__(pattern)

        self.imgs_path = ext.getConfig("imgs_path")
        self.imgs_extension = ext.getConfig("imgs_extension")

    def handleMatch(self, m, data):
        button_match = m.group(2) # Get the button abbreviation

        # Abort if the button abbreviation is not valid
        # Could also be done later with a try/catch, but doing it here avoids creating nodes that would go wasted
        if button_match not in self.BUTTON_NAMES:
            return None, None, None

        # Create span that will contain the image and text if needed
        e = etree.Element("span")
        e.attrib["class"] = self.SPAN_CLASS

        # Generate the img inside the span
        img_e = etree.SubElement(e, "img")
        img_e.attrib["src"] = f"{self.imgs_path}{button_match}.{self.imgs_extension}"
        img_e.attrib["alt"] = self.BUTTON_NAMES[button_match]
        # Get and check the type of match
        type_match = m.group(1)
        if type_match == "@!":
            # Return the span as is
            return e, m.start(0), m.end(0)
        elif type_match == "@!!":
            # Add text and return the span
            e.tail = "&nbsp;" + self.BUTTON_NAMES[button_match]
            return e, m.start(0), m.end(0)
        else:
            # This should be unreachable! If a breakpoint is hit here, it's probably a bug
            return None, None, None
