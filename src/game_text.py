from constant import *
import config
from exceptions import *


def add_game_message_to_print(ingame_message, message_color):
    """
    Adds game message to print

    Args:
        ingame_message (String): Message to add
        message_color (Color): Color of message
    """
    config.GAME_DATA.game_messages.append((ingame_message, message_color))


def text_height_helper(font):
    """
    Helper to retrieve height of font rect
    """
    font_object = font.render('a', False, (0, 0, 0))
    font_rect = font_object.get_rect()
    return font_rect.height


def messages_to_draw(message_list):
    """
    Store most recent NUM_MESSAGES in message_list in to_draw

    Args:
        message_list (List): List of messages to draw
    """
    if len(message_list) <= NUM_MESSAGES:
        to_draw = message_list
    else:
        to_draw = message_list[-NUM_MESSAGES:]
    return to_draw


def draw_text(display_surface, coord, text_color, text, text_bg_color=None, center=False):
    """
    displays text at coord on given surface

    Args:
        center (Boolean): If text should be centered
        display_surface (surface): surface to draw to
        coord ((int, int)): coord to draw to
        text_color (color): color of text
        text (string): text to draw
        text_bg_color (color): background color of text
    """
    text_surface, text_rect = _text_to_objects_helper(
        text, text_color, text_bg_color)

    if center:
        text_rect.center = coord
    else:
        text_rect.topleft = coord

    display_surface.blit(text_surface, text_rect)


def _text_to_objects_helper(inc_text, inc_color, inc_bg_color):
    """
    Helper function for draw_text. Returns the text surface and rect

    Args:
        inc_text (string): text to draw
        inc_color (color): color of text
        inc_bg_color (color): background color of text
    """
    if inc_bg_color:
        text_surface = FONT_DEBUG_MESSAGE.render(
            inc_text, False, inc_color, inc_bg_color)
    else:
        text_surface = FONT_DEBUG_MESSAGE.render(
            inc_text, False, inc_color, None )
    return text_surface, text_surface.get_rect()

# Taken from https://stackoverflow.com/questions/32590131/pygame-blitting-text-with-an-escape-character-or-newline
def multiLineSurface(string, font, rect, fontColour, BGColour, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Parameters
    ----------
    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rect style giving the size of the surface requested.
    fontColour - a three-byte tuple of the rgb value of the
             text color. ex (0, 0, 0) = BLACK
    BGColour - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                1 horizontally centered
                2 right-justified

    Returns
    -------
    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """
    finalLines = []
    requestedLines = string.splitlines()
    # Create a series of lines that will fit on the provided
    # rectangle.
    for requestedLine in requestedLines:
        if font.size(requestedLine)[0] > rect.width:
            words = requestedLine.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException("The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulatedLine = ""
            for word in words:
                testLine = accumulatedLine + word + " "
                # Build the line while the words fit.
                if font.size(testLine)[0] < rect.width:
                    accumulatedLine = testLine
                else:
                    finalLines.append(accumulatedLine)
                    accumulatedLine = word + " "
            finalLines.append(accumulatedLine)
        else:
            finalLines.append(requestedLine)

    # Let's try to write the text out on the surface.
    surface = pygame.Surface(rect.size)
    surface.fill(BGColour)
    accumulatedHeight = 0
    for line in finalLines:
        if accumulatedHeight + font.size(line)[1] >= rect.height:
            raise TextRectException("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempSurface = font.render(line, 1, fontColour)
        if justification == 0:
            surface.blit(tempSurface, (0, accumulatedHeight))
        elif justification == 1:
            surface.blit(tempSurface, ((rect.width - tempSurface.get_width()) / 2, accumulatedHeight))
        elif justification == 2:
            surface.blit(tempSurface, (rect.width - tempSurface.get_width(), accumulatedHeight))
        else:
            raise TextRectException("Invalid justification argument: " + str(justification))
        accumulatedHeight += font.size(line)[1]
    return surface


# Taken from https://stackoverflow.com/questions/32590131/pygame-blitting-text-with-an-escape-character-or-newline
def multiLineSurfaceTransparentBG(string, font, rect, fontColour, textBGColor=None, BGColour=None, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Parameters
    ----------
    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rect style giving the size of the surface requested.
    fontColour - a three-byte tuple of the rgb value of the
             text color. ex (0, 0, 0) = BLACK
    textBGColor - background color of text. None if text background is transparent
    BGColour - a three-byte tuple of the rgb value of the surface (not the actual background of text). None if
        background is transparent
    justification - 0 (default) left-justified
                1 horizontally centered
                2 right-justified

    Returns
    -------
    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.

    Args:
        textBGColor ():
        transparentColor ():
    """

    finalLines = []
    requestedLines = string.splitlines()
    # Create a series of lines that will fit on the provided
    # rectangle.
    for requestedLine in requestedLines:
        if font.size(requestedLine)[0] > rect.width:
            words = requestedLine.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException("The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulatedLine = ""
            for word in words:
                testLine = accumulatedLine + word + " "
                # Build the line while the words fit.
                if font.size(testLine)[0] < rect.width:
                    accumulatedLine = testLine
                else:
                    finalLines.append(accumulatedLine)
                    accumulatedLine = word + " "
            finalLines.append(accumulatedLine)
        else:
            finalLines.append(requestedLine)

    # Let's try to write the text out on the surface.
    surface = pygame.Surface(rect.size)
    if BGColour:
        surface.fill(BGColour)
    else:
        surface.set_colorkey(BLACK)
    accumulatedHeight = 0
    for line in finalLines:
        if accumulatedHeight + font.size(line)[1] >= rect.height:
            raise TextRectException("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempSurface = font.render(line, 1, fontColour, textBGColor)
        if justification == 0:
            surface.blit(tempSurface, (0, accumulatedHeight))
        elif justification == 1:
            surface.blit(tempSurface, ((rect.width - tempSurface.get_width()) / 2, accumulatedHeight))
        elif justification == 2:
            surface.blit(tempSurface, (rect.width - tempSurface.get_width(), accumulatedHeight))
        else:
            raise TextRectException("Invalid justification argument: " + str(justification))
        accumulatedHeight += font.size(line)[1]
    return surface