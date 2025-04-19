from PIL import Image
from io import BytesIO
from math import floor

import base64
import logging

logger = logging.getLogger("telebot")

def ImageToBytes(img: Image.Image):
    img_byte_arr = BytesIO()
    img_byte_arr.name = 'image.png'
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def ImageToBase64(image: Image.Image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = 'data:image/png;base64,' + str(base64.b64encode(buffered.getvalue()), 'utf-8')
    return img_base64

def RoundTo8(num):
    if num == 0:
        return 0
    else:
        multiple = round(num/8)
        return multiple * 8
    
def ConvertRatioToSize(base_size:int, ratio_x:float, ratio_y:float) -> tuple[int, int]:
    if ratio_x > ratio_y:
        ratio = ratio_x / ratio_y
        return (RoundTo8(base_size*ratio), RoundTo8(base_size))
    elif ratio_x < ratio_y:
        ratio = ratio_y / ratio_x
        return (RoundTo8(base_size), RoundTo8(base_size*ratio))
    else:
        ratio = ratio_x / ratio_y
        return (RoundTo8(base_size*ratio), RoundTo8(base_size*ratio))

def clamp(number, min, max):
    return min if number < min else max if number> max else number