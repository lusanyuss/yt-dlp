# python代码,加2方法  获取图img.png的长宽, 获取四角的坐标点
import io
import os
import random
import subprocess

import cv2
import numpy as np
from PIL import Image
from PIL import ImageDraw, ImageFont
from paddleocr import PaddleOCR


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

        # 使用指定的字体
        font = ImageFont.truetype(font_path, font_size_title)

        bbox = font.getmask(title).getbbox()
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算文本应该放置的位置
        x = img.width - text_width - 32  # 减去一些间距
        y = 32  # 加上一些间距

        # 以指定颜色绘制文本
        draw.text((x, y), title, font=font, fill=textColor)

        # 检查 output_img 是否有有效的扩展名
        output_img_ext = os.path.splitext(output_img)[1]
        if not output_img_ext:
            raise ValueError(f"Output file {output_img} does not have a valid extension")

        # 打印调试信息
        print(f"Saving image to {output_img} with extension {output_img_ext}")

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


def optimize_image_for_size(img, max_size=2 * 1024 * 1024, quality=85):
    """
    优化图像大小，确保不超过指定的最大大小。
    :param img: PIL Image对象。
    :param max_size: 最大文件大小（以字节为单位）。
    :param quality: 初始质量参数，用于JPEG图像。
    :return: 优化后的PIL Image对象。
    """
    # 尝试保存图像并检查大小
    img_temp = io.BytesIO()
    img.save(img_temp, format='JPEG', quality=quality)
    while img_temp.tell() > max_size and quality > 10:
        quality -= 5  # 降低质量以减小文件大小
        img_temp.seek(0)  # 重置文件指针
        img.save(img_temp, format='JPEG', quality=quality)

    img_temp.seek(0)  # 重置文件指针以供读取
    optimized_img = Image.open(img_temp)
    return optimized_img


def split_title_into_lines(title, max_chars_per_line):
    words = title.split(' ')
    lines = []
    current_line = ''
    for word in words:
        if len(current_line) + len(word) <= max_chars_per_line:
            current_line += word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def write_big_title(title, text_color, font_path, font_size_title, input_img, output_img, max_chars_per_line=7):
    # 打开图片
    with Image.open(input_img) as img:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, font_size_title)

        # 将标题拆分成多行，每行最多 max_chars_per_line 个字
        lines = split_title_into_lines(title, max_chars_per_line)

        # 如果只有两行且总字符数大于 max_chars_per_line
        if len(lines) == 2 and len(title) > max_chars_per_line:
            first_line_chars = len(title) % max_chars_per_line
            if first_line_chars == 0:
                first_line_chars = max_chars_per_line
            lines = [title[:first_line_chars]] + [title[first_line_chars:]]

        # 计算每行文本的高度和总文本块的高度
        line_height = font.getbbox('高')[3] - font.getbbox('高')[1]
        total_text_height = line_height * len(lines) + 16 * (len(lines) - 1)

        # 计算起始Y坐标，确保文本块底部与图片底部有16px间距
        y_start = img.height - total_text_height - 80

        # 逐行绘制文本
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (img.width - text_width) // 2
            y = y_start + i * (line_height + 16)

            draw.text((x, y), line, font=font, fill=text_color)

        # 在保存前优化图像大小
        optimized_img = optimize_image_for_size(img)

        # 保存优化后的图像
        optimized_img.save(output_img, quality=85)




# 示例调用方式


# 确保所有的导入
def has_chinese_characters(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)


def extract_and_print_chinese_text(output_path):
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    result = ocr.ocr(output_path, cls=True)
    chinese_text = ''
    if result and isinstance(result, list):
        for line in result:
            if line and isinstance(line, list):
                for word_info in line:
                    if word_info and isinstance(word_info, list):
                        word = word_info[1][0]
                        chinese_text += ''.join(filter(lambda x: '\u4e00' <= x <= '\u9fff', word))
    return chinese_text


def extract_frames(video_path, num_frames=3, crop_height=250):
    output_dir = os.path.dirname(video_path)

    # Get video duration
    command = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    command += ['-loglevel', 'quiet']
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    duration = float(result.stdout)

    # List to hold the paths of the frames
    frame_paths = []
    for i in range(num_frames):
        while True:
            time = random.randint(1, int(duration))
            output_path = os.path.join(output_dir, f"frame_{i + 1}.jpg")
            # 重用之前生成的,不重复生成了
            if os.path.exists(output_path) and not has_chinese_characters(extract_and_print_chinese_text(output_path)):
                frame_paths.append(output_path)
                break

            command = [
                'ffmpeg',
                '-v',
                'quiet',
                '-y',
                '-ss', str(time), '-i', video_path, '-frames:v', '1',
                '-q:v', '2', output_path
            ]
            command += ['-loglevel', 'quiet']
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')

            if os.path.exists(output_path):  # 确保图像已生成
                # 裁剪逻辑
                try:
                    image = Image.open(output_path)
                    original_width, original_height = image.size
                    new_height = original_height - crop_height
                    new_width = int(new_height * original_width / original_height)

                    left = (original_width - new_width) // 2
                    top = 0
                    right = left + new_width
                    bottom = top + new_height

                    cropped_image = image.crop((left, top, right, bottom))  # 按比例裁剪图片
                    cropped_image.save(output_path)

                    # OCR检查
                    chinese_text = extract_and_print_chinese_text(output_path)
                    if not has_chinese_characters(chinese_text):
                        # 提高图片分辨率
                        cropped_image_cv = cv2.cvtColor(np.array(cropped_image), cv2.COLOR_RGB2BGR)
                        sr = cv2.dnn_superres.DnnSuperResImpl_create()
                        model_path = "ESPCN_x3.pb"  # 预训练模型路径
                        sr.readModel(model_path)
                        sr.setModel("espcn", 3)  # 使用ESPCN模型，放大倍率为3
                        enhanced_image_cv = sr.upsample(cropped_image_cv)

                        # 调整回原始尺寸
                        enhanced_image_cv = cv2.resize(enhanced_image_cv, (original_width, original_height))
                        enhanced_image = Image.fromarray(cv2.cvtColor(enhanced_image_cv, cv2.COLOR_BGR2RGB))
                        enhanced_image.save(output_path)  # 保存分辨率提高后的图片

                        frame_paths.append(output_path)
                        break
                except Exception as e:
                    print(f"Error processing image {output_path}: {e}")
            else:
                print(f"Failed to generate frame at {output_path}")

    images = [Image.open(x) for x in frame_paths]
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    final_image_path = os.path.join(output_dir, 'input_img.jpg')
    new_im.save(final_image_path)
    print(f"Concatenated image saved as: {final_image_path}")

    # extract_and_print_chinese_text(frame_paths)


def print_image_size(image_path):
    """
    打印指定路径图像的尺寸和名称。

    参数:
    image_path (str): 图像文件的路径。
    """
    try:
        with Image.open(image_path) as img:
            # 获取图像尺寸
            width, height = img.size
            # 获取图像名称
            image_name = os.path.basename(image_path)
            print(f"图像名称: {image_name}, 图像尺寸: {width}x{height}")
    except Exception as e:
        print(f"无法打开图像。错误信息：{e}")


if __name__ == "__main__":

    # 尺寸=1280 x 720

    video_path = '../output_directory/video_68dafff0_mex23.mp4'  # 文件路径更新为放在 output_directory 目录下
    output_dir = 'extracted_frames'  # 指定保存帧的目录
    extract_frames(video_path, num_frames=3, crop_height=250)  # 提取帧的函数调用

    # 例子
    input_img = "../output_directory/input_img.jpg"
    print_image_size(input_img)
    # 转换图像格式
    try:
        with Image.open(input_img) as img:
            # 打印打开图像的格式和尺寸
            print(f"原始图像格式: {img.format}")
            print(f"原始图像尺寸: {img.size}")

            if img.format == 'JPEG':
                base_name = os.path.basename(input_img)
                dir_name = os.path.dirname(input_img)
                new_file_name = os.path.join(dir_name, os.path.splitext(base_name)[0] + '.png')

                # 保存为 PNG 格式
                img.save(new_file_name, 'PNG')
                print(f"{input_img} 已成功转换为 {new_file_name}")

                # 打印转换后图像的尺寸
                with Image.open(new_file_name) as new_img:
                    width, height = new_img.size
                    print(f"转换后图像格式: {new_img.format}")
                    print(f"转换后图像尺寸: {width}x{height}")
    except Exception as e:
        print(f"无法打开图像。错误信息：{e}")

    input_img = "../output_directory/input_img.png"

    # if is_resolution_gte_1920x1080(input_img):
    #     try:
    #         with Image.open(input_img) as img:
    #             # 获取图像的尺寸
    #             width, height = img.size
    #             # 指定的最大尺寸
    #             max_width, max_height = 1920, 1080
    #             # 如果图像尺寸大于指定的最大尺寸
    #             if width > max_width or height > max_height:
    #                 # 计算缩放比例
    #                 ratio = min(max_width / width, max_height / height)
    #                 new_width = int(width * ratio)
    #                 new_height = int(height * ratio)
    #                 # 缩放图像
    #                 img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    #                 # 保存缩放后的图像
    #                 img_resized.save(input_img)
    #     except Exception as e:
    #         print(f"无法处理图像。错误信息：{e}")
    #
    #
    #
    #
    #
    # if not is_resolution_gte_1920x1080(input_img):
    #     img = Image.open(input_img)
    #     img_resized = img.resize((1920, 1080), Image.Resampling.LANCZOS)
    #     img_resized.save(input_img)
    #
    # # 保证是1920*1080的图
    # if is_resolution_gte_1920x1080(input_img):
    #     print(f"{input_img} has a resolution greater than or equal to 1920x1080.")
    #     delete_files_if_exist([
    #         "../output_directory/output_img1.png",
    #         "../output_directory/output_img2.png",
    #         "../output_directory/output_big_img1.png",
    #         "../output_directory/横屏大图.png",
    #         "../output_directory/抖音三联屏_1.png",
    #         "../output_directory/抖音三联屏_2.png",
    #         "../output_directory/抖音三联屏_3.png"
    #     ])
    #
    #     # 先判断input_img的尺寸是不是宽高比,9:4,不是就切成9:4的宽高
    #     title = f"我真不是神仙啊"
    #
    #     # textColorTitle = "#FFFFFF"
    #     # textColor = "#FFFFFF"
    #
    #     textColorTitle = "#FFD700"
    #     textColor = "#FFD700"
    #
    #     font_size = 64 * 2
    #     font_title_size = 80 * 3
    #     # font_path = 'ziti/ttf/ChillRoundGothic_Medium.ttf'
    #     font_path = 'ziti/slideyouran/slideyouran_regular.ttf'
    #
    #     write_title(title, textColorTitle, font_path, font_title_size, input_img, "../output_directory/output_img1.png")
    #     write_numbers(textColor, font_path, font_size, '../output_directory/output_img1.png', '../output_directory/output_img2.png', '1')
    #     saved_segments = split_image_into_three("../output_directory/output_img2.png")
    #
    #     write_big_title(title, textColorTitle, font_path, font_title_size, "../output_directory/input_img.png", "../output_directory/output_big_img1.png")
    #     write_big_numbers(textColor, 'ziti/ttf/ChillRoundGothic_Medium.ttf', font_size, '../output_directory/output_big_img1.png',
    #                       '../output_directory/横屏大图.png', 'EP1-120')
    #
    #     delete_files_if_exist([
    #         "../output_directory/output_img1.png",
    #         "../output_directory/output_img2.png",
    #         "../output_directory/output_big_img1.png"
    #     ])
