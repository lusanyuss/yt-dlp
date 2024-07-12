import os

from PIL import Image, ImageDraw, ImageFont


def create_artistic_text(output_path, text, font_path):
    width, height = 300, 300  # 或者根据需要调整
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    font_size = 100  # 字体大小
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, font=font, fill="black")

    image.save(output_path)


if __name__ == "__main__":
    # 使用方法
    font_path = os.path.join('ziti', 'MonuTitl', 'MonuTitl-0.95CnBd.ttf')
    output_path = 'artistic_text.png'
    text = '艺术'
    create_artistic_text(output_path, text, font_path)
