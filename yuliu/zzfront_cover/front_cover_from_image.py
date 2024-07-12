# python代码,加2方法  获取图img.png的长宽, 获取四角的坐标点

import os

from PIL import ImageDraw, ImageFont
from PIL import Image


def is_resolution_gte_1920x1080(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        print(f"Image width: {width}, Image height: {height}")  # 打印图片的宽度和高度
        return width >= 1920 and height >= 1080


def delete_files_if_exist(files_list):
    for file_name in files_list:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Deleted {file_name}")
        else:
            print(f"{file_name} does not exist")


def get_image_dimensions(image_path):
    """
    获取图像的尺寸（宽度和高度）。

    参数:
        image_path (str): 图像的路径。

    返回:
        tuple: (width, height)
    """
    with Image.open(image_path) as img:
        return img.size


def get_corner_coordinates(width, height):
    """
    获取图像四角的坐标点。

    参数:
        width (int): 图像的宽度。
        height (int): 图像的高度。

    返回:
        dict: 包含四个角的坐标点。
    """
    return {
        "top_left": (0, 0),
        "top_right": (width - 1, 0),
        "bottom_left": (0, height - 1),
        "bottom_right": (width - 1, height - 1)
    }


def split_image_into_three(image_path):
    """
    将图片竖直地分成三份并获取这三张图片的坐标点。

    参数:
        image_path (str): 图像的路径。

    返回:
        list: 包含三个坐标点的元组，每个元组代表一个分片的左上和右下坐标点。
    """
    width, height = get_image_dimensions(image_path)
    segment_width = width // 3

    segments = []
    for i in range(3):
        top_left = (i * segment_width, 0)
        if i == 2:  # 对于最后一份，确保捕获所有剩余的像素
            bottom_right = (width, height)
        else:
            bottom_right = ((i + 1) * segment_width, height)
        segments.append((top_left, bottom_right))

    return segments


def split_image_into_three(image_path, save_path_prefix="抖音三联屏"):
    """
    将图片竖直地分成三份并保存它们。

    参数:
        image_path (str): 图像的路径。
        save_path_prefix (str): 保存分割图像的文件名前缀。

    返回:
        list: 三个新文件的路径。
    """
    with Image.open(image_path) as img:
        width, height = img.size
        segment_width = width // 3

        saved_files = []
        for i in range(3):
            left = i * segment_width
            if i == 2:  # 对于最后一份，确保捕获所有剩余的像素
                right = width
            else:
                right = (i + 1) * segment_width

            # 根据坐标点裁剪图片
            segment = img.crop((left, 0, right, height))
            file_name = f"{save_path_prefix}_{i + 1}.png"
            segment.save(file_name)
            saved_files.append(file_name)

        return saved_files


def write_title(title, textColor, font_path, font_size_title, input_img, output_img):
    # 打开图片
    with Image.open(input_img) as img:
        draw = ImageDraw.Draw(img)

        # 使用内置的字体。如果要使用其他字体，可以使用ImageFont.truetype('path_to_font.ttf', size)
        # 这只是一个示例值，可能需要根据实际需求调整
        font = ImageFont.truetype(font_path, font_size_title)  # 使用Arial字体

        bbox = font.getmask(title).getbbox()
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算文本应该放置的位置
        x = img.width - text_width - 32  # 减去10为了从右边留出一点间距
        y = 32  # 加上10为了从顶部留出一点间距

        # 以白色绘制文本
        draw.text((x, y), title, font=font, fill=textColor)

        # 保存图像
        img.save(output_img)


def write_numbers(text_color, font_path, font_size, input_path, output_path, text):
    # 打开图片
    image = Image.open(input_path)
    width, height = image.size
    draw = ImageDraw.Draw(image)

    # 计算中间的横线位置，但不绘制
    horizontal_line_y = height // 2

    # 计算两条竖线的位置，但不绘制
    part_width = width // 3

    # 使用指定的字体和大小
    font = ImageFont.truetype(font_path, font_size)

    for i in range(3):
        x_center = part_width * (i + 0.5)
        y_center = horizontal_line_y + height // 4

        # 用中心坐标计算bbox
        bbox = draw.textbbox((x_center, y_center), text, font=font, anchor="mm")
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        x = x_center - text_width / 2
        y = y_center - text_height / 2
        draw.text((x, y), str(i + 1), font=font, fill=text_color)

    image.save(output_path)


def write_big_title(title, textColor, font_path, font_size_title, input_img, output_img):
    # 打开图片
    with Image.open(input_img) as img:
        draw = ImageDraw.Draw(img)

        # 使用ImageFont.truetype加载字体文件并设置字体大小
        font = ImageFont.truetype(font_path, font_size_title)

        # 计算文本的宽度和高度
        bbox = font.getmask(title).getbbox()
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算文本应该放置的位置
        x = (img.width / 2) - (text_width / 2)  # 图片的中心位置，再减去文本宽度的一半，让文本在x方向上居中
        y = (img.height / 4) - (text_height / 2)  # 图片上半部分的中心位置，再减去文本高度的一半，让文本在y方向上居中

        # 绘制文本
        draw.text((x, y), title, font=font, fill=textColor)

        # 保存图像
        img.save(output_img)


def write_big_numbers(text_color, font_path, font_size, input_path, output_path, text):
    # 打开图片
    image = Image.open(input_path)
    width, height = image.size
    draw = ImageDraw.Draw(image)

    # 计算中间的横线位置，但不绘制
    horizontal_line_y = height // 2

    # 计算两条竖线的位置，但不绘制
    part_width = width // 3

    # 使用指定的字体和大小
    font = ImageFont.truetype(font_path, font_size)

    # 只在2的位置绘制
    i = 1
    x_center = part_width * (i + 0.5)
    y_center = horizontal_line_y + height // 4

    # 用中心坐标计算bbox
    bbox = draw.textbbox((x_center, y_center), text, font=font, anchor="mm")
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = x_center - text_width / 2
    y = y_center - text_height / 2
    draw.text((x, y), text, font=font, fill=text_color)

    image.save(output_path)


if __name__ == "__main__":
    # 例子
    input_img = "input_img.jpg"
    if is_resolution_gte_1920x1080(input_img):
        try:
            with Image.open(input_img) as img:
                # 获取图像的尺寸
                width, height = img.size
                # 指定的最大尺寸
                max_width, max_height = 1920, 1080
                # 如果图像尺寸大于指定的最大尺寸
                if width > max_width or height > max_height:
                    # 计算缩放比例
                    ratio = min(max_width / width, max_height / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    # 缩放图像
                    img_resized = img.resize((new_width, new_height), Image.ANTIALIAS)
                    # 保存缩放后的图像
                    img_resized.save(input_img)
        except Exception as e:
            print(f"无法处理图像。错误信息：{e}")

    try:
        with Image.open(input_img) as img:
            if img.format == 'JPEG':
                base_name = os.path.basename(input_img)
                dir_name = os.path.dirname(input_img)
                new_file_name = os.path.join(dir_name, os.path.splitext(base_name)[0] + '.png')
                img.save(new_file_name, 'PNG')
                print(f"{input_img} 已成功转换为 {new_file_name}")
    except Exception as e:
        print(f"无法打开图像。错误信息：{e}")

    if not is_resolution_gte_1920x1080(input_img):
        img = Image.open(input_img)
        img_resized = img.resize((1920, 1080), Image.ANTIALIAS)
        img_resized.save(input_img)

    # 保证是1920*1080的图
    if is_resolution_gte_1920x1080(input_img):
        print(f"{input_img} has a resolution greater than or equal to 1920x1080.")
        delete_files_if_exist([
            "output_img1.png",
            "output_img2.png",
            "output_big_img1.png",
            "横屏大图.png",
            "抖音三联屏_1.png",
            "抖音三联屏_2.png",
            "抖音三联屏_3.png"
        ])

        # 先判断input_img的尺寸是不是宽高比,9:4,不是就切成9:4的宽高
        title = "极速追杀4"
        # textColorTitle = "#FDFE09"
        textColorTitle = "#FFFFFF"
        textColor = "#FFFFFF"
        # textColor = "#000000"
        font_size = 128
        font_title_size = 192
        font_path = 'ziti/slideyouran/slideyouran_regular.ttf'

        write_title(title, textColorTitle, font_path, font_title_size, input_img, "output_img1.png")
        write_numbers(textColor, font_path, font_size, 'output_img1.png', 'output_img2.png', '1')
        saved_segments = split_image_into_three("output_img2.png")

        write_big_title(title, textColorTitle, font_path, font_title_size, "input_img.png", "output_big_img1.png")
        write_big_numbers(textColor, font_path, font_size, 'output_big_img1.png', '横屏大图.png', '')

        delete_files_if_exist([
            "output_img1.png",
            "output_img2.png",
            "output_big_img1.png"
        ])
