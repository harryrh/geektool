#
# Some simple image related utilities
#
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Align one box inside another bounding box
# Returns the (x,y) offset of the size inside the bounds
def align(size, bounds, halign, valign):
    if halign == 'left':
        x = 0
    elif halign == 'center':
        x = bounds[0] / 2 - size[0] / 2
    elif halign == 'right':
        x = bounds[0] - size[0]
    else:
        raise Exception('What is halign="%s"' % halign)

    if valign == 'top':
        y = 0            
    elif valign == 'bottom':
        y = bounds[1] - size[1]
    elif valign == 'center':
        y = bounds[1] / 2 - size[1] / 2
    else:
        raise Exception('What is valign="%s"' % valign)

    return (x, y)

def horizontal_montage(images, 
        spacing=0,
        min_width=0,
        min_height=0,
        halign='center',
        valign='center',
        mode='RGBA',
        color=0,
        samewidth=False):
    '''Merge images together horizontally (left to right)'''

    # Determine new image size
    (width, height) = (0, 0)

    source_sizes = [i.size for i in images]
    source_max_width = max(i[0] for i in source_sizes)
    source_max_height = max(i[1] for i in source_sizes)

    if samewidth:
        box_widths = [max(min_width, source_max_width)] * len(source_sizes)
    else:
        box_widths = [max(min_width, i[0]) for i in source_sizes]

    box_heights = [max(min_height, source_max_height)] * len(source_sizes)

    boxes = zip(box_widths, box_heights)

    width = sum(box_widths) + spacing * (len(images) - 1)
    height = max(box_heights)

    montage = Image.new(mode, (width, height), color)

    # Box => (image, width, right)
    # Paste images together into the new image
    (x, y) = (0, 0)
    for i, image in enumerate(images):
        (xo, yo) = align(image.size, boxes[i], halign, valign)
        montage.paste(image, (x+xo, y+yo))
        x = x + boxes[i][0] + spacing

    return montage

def vertical_montage(images, 
        spacing=0,
        min_width=0,
        min_height=0,
        halign='center',
        valign='center',
        mode='RGBA',
        color=0,
        sameheight=False):
    '''Merge images vertically (top to bottom)'''

    # Determine new image size
    (width, height) = (0, 0)

    source_sizes = [i.size for i in images]
    source_max_width = max(i[0] for i in source_sizes)
    source_max_height = max(i[1] for i in source_sizes)

    if sameheight:
        box_heights = [max(min_height, source_max_height)] * len(source_sizes)
    else:
        box_heights = [max(min_height, i[1]) for i in source_sizes]

    box_widths = [max(min_width, source_max_width)] * len(source_sizes)

    boxes = zip(box_widths, box_heights)

    height = sum(box_heights) + spacing * (len(images) - 1)
    width = max(box_widths)

    montage = Image.new(mode, (width, height), color)

    # Box => (image, width, right)
    # Paste images together into the new image
    (x, y) = (0, 0)
    for i, image in enumerate(images):
        (xo, yo) = align(image.size, boxes[i], halign, valign)
        montage.paste(image, (x+xo, y+yo))
        y = y + boxes[i][1] + spacing

    return montage

def text_as_image(text, font=ImageFont.load_default(), fill=None, mode='RGBA'):
    size = font.getsize(text)

    image = Image.new(mode, size)
    draw = ImageDraw.Draw(image)
    draw.text((0,0), text, font=font, fill=fill)

    return image

def drop_shadow(image, color='black', offset=(2,3), blur=2):
    (w, h) = image.size

    original = image

    new_width = w + abs(offset[0])
    new_height = h + abs(offset[1])

    new_image = Image.new('RGBA', (new_width, new_height))

    image_x = abs(min(0, offset[0]))
    image_y = abs(min(0, offset[1]))

    shadow_x = max(0, offset[0])
    shadow_y = max(0, offset[1])
        
    new_image.paste(original, (image_x, image_y, original.size[0], original.size[1]))
    alpha = new_image.split()[3]

    highlight = Image.new('RGBA', new_image.size, color)
    highlight.putalpha(alpha)
    blurred = highlight
    for i in xrange(blur):
        blurred = blurred.filter(ImageFilter.BLUR)

    final = Image.new('RGBA', new_image.size)
    final.paste(blurred, (shadow_x, shadow_y))
    final.paste(new_image, (image_x, image_y), alpha)

    return final

def circlegauge(width, height, value, 
        value_min=0.0, value_max=1.0, 
        background=None, foreground='white',
        stroke=1,
        startangle=0,
        text=None, font=ImageFont.load_default(), fontcolor='white'):

    percent = (float(value) - value_min) / (value_max - value_min)
    degrees = int(percent * 360)

    im = Image.new('RGBA', (width, height), 0)
    draw = ImageDraw.Draw(im)
    if background:
        draw.ellipse((0,0,width,height), fill=background)
    draw.pieslice((0,0,width,height), startangle, startangle+degrees, fill=foreground)
    draw.ellipse((stroke,stroke,width-stroke,height-stroke), fill=0)

    if text:
        (fw,fh) = font.getsize(text)
        draw.text((width/2-fw/2,height/2-fh/2), text, font=font, fill=fontcolor)

    return im

