from fcntl import ioctl
from PIL import Image, ImageDraw, ImageFont
from main import hw_info
import mmap
import os

fb: int
mm: mmap.mmap

screen_resolutions = {
    1: (720, 720, 16),
    2: (720, 480, 9)
}

screen_width, screen_height, max_elem = screen_resolutions.get(hw_info, (640, 480, 9))
bytes_per_pixel = 4
screen_size = screen_width * screen_height * bytes_per_pixel
fb_screeninfo = None

script_dir = os.path.dirname(os.path.abspath(__file__))
font_file = os.path.join(script_dir, 'font', 'font.ttf')
if not os.path.exists(font_file):
    font_file = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"

colorBlue = "#bb7200"
colorBlueD1 = "#7f4f00"
colorGray = "#292929"
colorGrayL1 = "#383838"
colorGrayD2 = "#141414"
colorGreen = "#00ff00"
colorRed = "#0202cb"

activeImage: Image.Image
activeDraw: ImageDraw.ImageDraw


def get_fb_screeninfo():
    global fb_screeninfo
    if os.path.exists('/mnt/mod/ctrl/configs/fb.cfg'):
        with open('/mnt/mod/ctrl/configs/fb.cfg', 'rb') as file:
            fb_screeninfo = file.read()
    elif hw_info == 1:
        fb_screeninfo = b'\xd0\x02\x00\x00\xd0\x02\x00\x00\xd0\x02\x00\x00\xa0\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00F_\x00\x008\x00\x00\x00J\x00\x00\x00\x0f\x00\x00\x00<\x00\x00\x00\n\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 2:
        fb_screeninfo = b'\xd0\x02\x00\x00\xe0\x01\x00\x00\xd0\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00=\x96\x00\x00,\x00\x00\x006\x00\x00\x00\x0f\x00\x00\x00$\x00\x00\x00\x02\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 3:
        fb_screeninfo = b'\xe0\x01\x00\x00\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 4:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 5:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\n\x00\x00\x00"\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 6:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00(\x00\x00\x00 \x00\x00\x00,\x00\x00\x00 \x00\x00\x00\x08\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 7:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0b\x00\x00\x00\x1b\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 8:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0b\x00\x00\x00\x1b\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    elif hw_info == 9:
        fb_screeninfo = b'\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    else:
        fb_fd = os.open("/dev/fb0", os.O_RDWR)
        try:
            fb_info = bytearray(160)
            ioctl(fb_fd, 0x4600, fb_info)
            fb_screeninfo = bytes(fb_info)
        finally:
            os.close(fb_fd)
    #print(fb_screeninfo)
    return fb_screeninfo

def screen_reset():
    if fb_screeninfo is not None:
        ioctl(
            fb,
            0x4601,
            bytearray(fb_screeninfo),
        )
    ioctl(fb, 0x4611, 0)


def draw_start():
    global fb, mm
    fb = os.open("/dev/fb0", os.O_RDWR)
    mm = mmap.mmap(fb, screen_size)


def draw_end():
    global fb, mm
    mm.close()
    os.close(fb)


def create_image():
    image = Image.new("RGBA", (screen_width, screen_height), color="black")
    return image


def draw_active(image):
    global activeImage, activeDraw
    activeImage = image
    activeDraw = ImageDraw.Draw(activeImage)


def draw_paint():
    global activeImage
    if hw_info == 3:
        img = activeImage.rotate(90, expand=True)
        mm.seek(0)
        mm.write(img.tobytes())
    else:
        mm.seek(0)
        mm.write(activeImage.tobytes())


def draw_clear():
    global activeDraw
    activeDraw.rectangle((0, 0, screen_width, screen_height), fill="black")


def draw_text(position, text, font=15, color="white", **kwargs):
    global activeDraw
    activeDraw.text(position, text, font=ImageFont.truetype(font_file, font), fill=color, **kwargs)


def draw_rectangle(position, fill=None, outline=None, width=1):
    global activeDraw
    activeDraw.rectangle(position, fill=fill, outline=outline, width=width)


def draw_rectangle_r(position, radius, fill=None, outline=None):
    global activeDraw
    activeDraw.rounded_rectangle(position, radius, fill=fill, outline=outline)


def draw_circle(position, radius, fill=None, outline="white"):
    global activeDraw
    activeDraw.ellipse(
        [position[0], position[1], position[0] + radius, position[1] + radius],
        fill=fill,
        outline=outline,
    )


def draw_log(text, fill="Black", outline="black", width=500, font=15):
    x = (screen_width - width) / 2
    y = (screen_height - 80) / 2
    rect_height = 80
    draw_rectangle_r([x, y, x + width, y + 80], 5, fill=fill, outline=outline)

    font_obj = ImageFont.truetype(font_file, font)
    padding = 10
    max_width = width - 2 * padding

    lines = []
    current_line = ""
    for word in text.split():
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = font_obj.getbbox(test_line)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = ""
            
            bbox = font_obj.getbbox(word)
            word_width = bbox[2] - bbox[0]
            if word_width <= max_width:
                current_line = word
            else:
                remaining = word
                while remaining:
                    substring = ""
                    for char in remaining:
                        temp_sub = substring + char
                        bbox = font_obj.getbbox(temp_sub)
                        temp_width = bbox[2] - bbox[0]
                        if temp_width <= max_width:
                            substring = temp_sub
                        else:
                            break
                    if substring:
                        lines.append(substring)
                        remaining = remaining[len(substring):]
                    else:
                        break
    if current_line:
        lines.append(current_line)

    bbox = font_obj.getbbox("A")
    line_height = bbox[3] - bbox[1]
    total_height = len(lines) * line_height
    start_y = y + (rect_height - total_height) // 2

    for i, line in enumerate(lines):
        text_x = x + width / 2
        text_y = start_y + i * line_height + 10
        draw_text((text_x, text_y), line, font, anchor="mm")


def draw_help(text, fill="Black", outline="black", font=15):
    x = 20
    y = (screen_height - 110)
    rect_width = screen_width - 40
    rect_height = 75
    draw_rectangle_r([x, y, screen_width - 20, y + rect_height], 5, fill=fill, outline=outline)

    font_obj = ImageFont.truetype(font_file, font)
    padding = 10
    max_width = rect_width - 2 * padding

    lines = []
    current_line = ""
    for word in text.split():
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = font_obj.getbbox(test_line)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = ""
            
            bbox = font_obj.getbbox(word)
            word_width = bbox[2] - bbox[0]
            if word_width <= max_width:
                current_line = word
            else:
                remaining = word
                while remaining:
                    substring = ""
                    for char in remaining:
                        temp_sub = substring + char
                        bbox = font_obj.getbbox(temp_sub)
                        temp_width = bbox[2] - bbox[0]
                        if temp_width <= max_width:
                            substring = temp_sub
                        else:
                            break
                    if substring:
                        lines.append(substring)
                        remaining = remaining[len(substring):]
                    else:
                        break
    if current_line:
        lines.append(current_line)

    bbox = font_obj.getbbox("A")
    line_height = bbox[3] - bbox[1]
    total_height = len(lines) * line_height
    start_y = y + (rect_height - total_height) // 2

    for i, line in enumerate(lines):
        text_x = screen_width // 2
        text_y = start_y + i * line_height +10
        draw_text((text_x, text_y), line, font, anchor="mm")


def display_image(image_path, target_x=0, target_y=0, target_width=None, target_height=None, rota=1):
    global activeImage
    if target_width is None:
        target_width = screen_width - target_x
    if target_height is None:
        target_height = screen_height - target_y
    img = Image.open(image_path)
    img.thumbnail((target_width, target_height))
    img = img.convert('RGBA')
    r, g, b, a = img.split()
    img = Image.merge('RGBA', (b, g, r, a))
    paste_x = target_x + (target_width - img.width) // 2
    paste_y = target_y + (target_height - img.height) // 2
    if hw_info == 3 and rota == 1:
        img = img.rotate(-90, expand=True)
    activeImage.paste(img, (paste_x, paste_y))
    draw_paint()


fb_screeninfo = get_fb_screeninfo()

draw_start()
screen_reset()

imgMain = create_image()
draw_active(imgMain)
