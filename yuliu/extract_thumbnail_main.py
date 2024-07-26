import io
import os
import random
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from paddleocr import PaddleOCR

from yuliu.utils import resize_images_if_needed, convert_jpeg_to_png, print_separator


def is_resolution_gte_1920x1080(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        return width >= 1920 and height >= 1080


def delete_files_if_exist(files_list):
    for file_name in files_list:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"删除文件: {file_name}")
        else:
            print(f"{file_name} 不存在")


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


# 示例调用方式


# 确保所有的导入
def has_chinese_characters(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)


def extract_and_print_chinese_text(output_path):
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
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


def get_cover_images(frame_images, output_dir):
    frame_images_length = len(frame_images)
    if frame_images_length % 3 != 0:
        raise ValueError("Number of frames must be a multiple of 3")
    batch_size = 3
    for i in range(0, frame_images_length, batch_size):
        batch_paths = frame_images[i:i + batch_size]
        images = [Image.open(x) for x in batch_paths]
        widths, heights = zip(*(im.size for im in images))

        total_width = sum(widths)
        max_height = max(heights)

        new_im = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        batch_index = ''.join([str(j + 1) for j in range(i, i + batch_size)])
        final_image_path = os.path.join(output_dir, f'input_img{batch_index}.jpg')
        new_im.save(final_image_path)

    return [os.path.join(output_dir, f'input_img{"".join([str(j + 1) for j in range(i, i + batch_size)])}.jpg') for i in
            range(0, frame_images_length, batch_size)]


def generate_frame(index, video_path, duration, output_dir, crop_height, model_path, frame_paths, lock):
    output_path = os.path.join(output_dir, f"frame_{index + 1}.jpg")
    if os.path.exists(output_path):
        with lock:
            frame_paths[index] = output_path
            print(f"文件 frame_{index + 1}.jpg 已存在,直接返回: {output_path}")
            return

    while True:
        command = [
            'ffmpeg',
            '-y',
            '-ss', str(random.randint(1, int(duration))), '-i', video_path, '-frames:v', '1',
            '-q:v', '2', output_path,
            '-loglevel', 'quiet'
        ]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')

        if os.path.exists(output_path):
            try:
                image = Image.open(output_path)
                original_width, original_height = image.size
                new_height = original_height - crop_height
                new_width = int(new_height * original_width / original_height)

                left = (original_width - new_width) // 2
                top = 0
                right = left + new_width
                bottom = top + new_height

                cropped_image = image.crop((left, top, right, bottom))
                cropped_image.save(output_path)
                chinese_text = extract_and_print_chinese_text(output_path)

                if not has_chinese_characters(chinese_text):
                    cropped_image_cv = cv2.cvtColor(np.array(cropped_image), cv2.COLOR_RGB2BGR)
                    sr = cv2.dnn_superres.DnnSuperResImpl_create()
                    sr.readModel(model_path)
                    sr.setModel("espcn", 3)
                    enhanced_image_cv = sr.upsample(cropped_image_cv)
                    enhanced_image_cv = cv2.resize(enhanced_image_cv, (original_width, original_height))
                    enhanced_image = Image.fromarray(cv2.cvtColor(enhanced_image_cv, cv2.COLOR_BGR2RGB))
                    enhanced_image.save(output_path)
                    with lock:
                        frame_paths[index] = output_path
                        print(f"\n重新生成 frame_{index + 1}.jpg 图片: {output_path} \n")
                    break
            except Exception as e:
                print(f"Error processing image {output_path}: {e}")
        else:
            print(f"Failed to generate frame at {output_path}")


def get_frame_images(num_frames, video_path, duration, output_dir, crop_height, model_path, timeout_duration):
    frame_paths = [None] * num_frames
    lock = threading.Lock()

    def timeout_handler():
        print(f"在 {timeout_duration} 秒内未能完成所有任务，返回空的数据。")
        nonlocal frame_paths
        frame_paths = [None] * num_frames
        # 取消所有正在进行的任务
        executor.shutdown(wait=False, cancel_futures=True)

    timer = threading.Timer(timeout_duration, timeout_handler)
    timer.start()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [
            executor.submit(generate_frame, i, video_path, duration, output_dir, crop_height, model_path, frame_paths, lock)
            for i in range(num_frames)
        ]
        try:
            for future in as_completed(futures):
                future.result()  # 处理可能的异常
        except Exception as e:
            print(f"任务执行过程中出现异常: {e}")
        finally:
            timer.cancel()  # 如果任务在超时前完成，取消定时器

    return frame_paths


def extract_covers_and_frames(video_path, release_video_dir, num_frames=3 * 1, crop_height=0):
    # Get video duration
    command = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    command += ['-loglevel', 'quiet']
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    duration = float(result.stdout)

    # Model path for super resolution
    model_path = "ESPCN_x3.pb"
    timeout_duration = num_frames * 50
    images_dir = os.path.join(release_video_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 截图列表
    frame_images = get_frame_images(num_frames, video_path, duration, images_dir, crop_height, model_path, timeout_duration)
    # 封面图列表
    cover_images = []
    if len(frame_images) == num_frames:
        cover_images = get_cover_images(frame_images, images_dir)
    else:
        delete_files(frame_images)
        frame_images = []
    return cover_images, frame_images


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


def check_and_crop_images(frame_paths):
    """
    检查并裁剪一组图像，使其符合指定的宽高比，同时确保尽可能多的画面内容显示。

    参数：
    - frame_paths: list, 包含图像文件路径的列表。

    返回值：
    - 无
    """
    # 预期的宽高比
    ratios = [
        427 / 720,
        426 / 720,
        427 / 720
    ]

    for i, path in enumerate(frame_paths):
        expected_ratio = ratios[i % len(ratios)]

        with Image.open(path) as img:
            width, height = img.size
            current_ratio = width / height

            # 计算需要的宽度和高度以匹配期望的比例
            if current_ratio > expected_ratio:
                # 当前图像过宽，需要裁剪宽度
                new_width = int(height * expected_ratio)
                new_height = height
                left = (width - new_width) // 2
                top = 0
            else:
                # 当前图像过高，需要裁剪高度
                new_width = width
                new_height = int(width / expected_ratio)
                left = 0
                top = (height - new_height) // 2

            right = left + new_width
            bottom = top + new_height

            # 裁剪图像，确保中心部分显示
            cropped_img = img.crop((left, top, right, bottom))
            cropped_img.save(path)
            print(f"Cropped image saved as: {path}")


def get_unique_path(dst_path):
    """生成唯一的文件路径，以避免覆盖现有文件"""
    base, ext = os.path.splitext(dst_path)
    counter = 1
    unique_path = dst_path
    while os.path.exists(unique_path):
        unique_path = f"{base}_{counter}{ext}"
        counter += 1
    return unique_path


def delete_files(file_paths):
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
            else:
                print(f"文件不存在: {file_path}")
        except Exception as e:
            print(f"删除 {file_path} 时出错: {e}")


def move_images_to_release(cover_images, frame_images, release_video_dir):
    """移动cover_images和frame_images中的图片到release_video目录"""
    # 确保输出目录存在
    os.makedirs(release_video_dir, exist_ok=True)

    # cover_image_list = []
    # frame_image_list = []
    # 移动cover_images中的图片
    # for src_path in cover_images:
    #     if os.path.exists(src_path) and os.path.isfile(src_path):
    #         filename = os.path.basename(src_path)
    #         dst_path = os.path.join(release_video_dir, filename)
    #         unique_dst_path = dst_path
    #         shutil.copy(src_path, unique_dst_path)
    #         cover_image_list.append(unique_dst_path)
    #         print(f"移动文件: {src_path} 到 {unique_dst_path}")
    # 移动frame_images中的图片
    # for src_path in frame_images:
    #     if os.path.exists(src_path) and os.path.isfile(src_path):
    #         filename = os.path.basename(src_path)
    #         dst_path = os.path.join(release_video_dir, filename)
    #         unique_dst_path = dst_path
    #         shutil.copy(src_path, unique_dst_path)
    #         frame_image_list.append(unique_dst_path)
    #         print(f"移动文件: {src_path} 到 {unique_dst_path}")

    return frame_images


def check_images_in_release_dir(release_video_dir, number_covers=1):
    # 定义匹配文件名的正则表达式
    input_img_pattern = re.compile(r'^input_img\d+\.png$')
    frame_pattern = re.compile(r'^frame_\d+\.jpg$')
    # 获取目录中的所有文件
    files = os.listdir(release_video_dir)
    # 过滤出符合条件的文件
    input_img_files = [file for file in files if input_img_pattern.match(file)]
    frame_files = [file for file in files if frame_pattern.match(file)]

    # 检查是否满足条件
    if len(input_img_files) >= number_covers and len(frame_files) >= 3 * number_covers:
        print(f"目录中已存在 {number_covers} 张满足条件的 input_img 文件和 {3 * number_covers} 张 frame 文件，退出方法。")
        return True
    else:
        print(
            f"目录中没有找到足够的图片文件，需要 {number_covers} 张 input_img 文件和 {3 * number_covers} 张 frame 文件，但仅找到 {len(input_img_files)} 张 input_img 文件和 {len(frame_files)} 张 frame 文件。")
        return False


from PIL import Image, ImageDraw, ImageFont


def write_big_title(title, subtitle, title_color, subtitle_color, font_path, subtitle_font, font_size, subtitle_font_size, cover_image, border_width=3,
                    border_color='black'):
    title = title.strip()
    subtitle = subtitle.strip()

    draw = ImageDraw.Draw(cover_image)
    font = ImageFont.truetype(font_path, font_size)
    subtitle_font = ImageFont.truetype(subtitle_font, subtitle_font_size)

    beilv = 0.05
    margin_left = int(cover_image.width * beilv)
    margin_right = int(cover_image.width * beilv)
    margin_bottom = int(cover_image.height * beilv)
    text_area_width = cover_image.width - margin_left - margin_right

    if ',' in title:
        lines = title.split(',')
    else:
        avg_char_width = draw.textbbox((0, 0), '测试', font=font)[2] // 2
        max_chars_per_line = text_area_width // avg_char_width

        total_chars = len(title)
        if max_chars_per_line == 0:
            max_chars_per_line = 1
        total_lines = (total_chars + max_chars_per_line - 1) // max_chars_per_line

        lines = []
        first_line_length = total_chars - (total_lines - 1) * max_chars_per_line
        if first_line_length > max_chars_per_line:
            first_line_length = max_chars_per_line
        start_idx = 0

        lines.append(title[start_idx:start_idx + first_line_length])
        start_idx += first_line_length

        while start_idx < total_chars:
            lines.append(title[start_idx:start_idx + max_chars_per_line])
            start_idx += max_chars_per_line

    line_spacing = font_size * 0.2
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
    total_height = sum(line_heights) + line_spacing * (len(lines) - 1)

    y_text = cover_image.height - margin_bottom - total_height

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = line_heights[i]
        x_text = (cover_image.width - width) / 2

        # 绘制边框
        for dx in range(-border_width, border_width + 1):
            for dy in range(-border_width, border_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x_text + dx, y_text + dy), line, font=font, fill=border_color)

        # 绘制文字
        draw.text((x_text, y_text), line, font=font, fill=title_color)
        y_text += height + line_spacing

    subtitle_margin_top = int(cover_image.height * beilv)
    subtitle_margin_right = int(cover_image.width * beilv)

    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_x = cover_image.width - subtitle_margin_right - subtitle_bbox[2]
    subtitle_y = subtitle_margin_top

    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            if dx != 0 or dy != 0:
                draw.text((subtitle_x + dx, subtitle_y + dy), subtitle, font=subtitle_font, fill=border_color)

    draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=subtitle_color)

    return cover_image


# 示例用法


import re


def delete_matching_images(directory):
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        # 检查文件名是否以 .png 或 .jpg 结尾
        if filename.endswith('.png') or filename.endswith('.jpg'):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")


def process_image(image, cover_path):
    image.save(cover_path)
    if os.path.exists(cover_path) and os.path.getsize(cover_path) > 2 * 1024 * 1024:
        with Image.open(cover_path) as img:
            img = img.resize((1280, 720), Image.LANCZOS)
            img.save(cover_path, optimize=True, quality=85)
        file_size = os.path.getsize(cover_path) / (1024 * 1024)


def adjust_title(title, kongge='　'):
    if ',' in title:
        return title
    title_len = len(title)
    if title_len == 2:
        return title[0] + kongge * 2 + title[1]
    elif title_len == 3:
        return title[0] + kongge + title[1] + kongge + title[2]
    return title


def replace_subtitle(subtitle):
    choices = [80, 85, 90, 95, 100, 110, 120]
    random_number = random.choice(choices)
    new_subtitle = subtitle.replace("120", str(random_number))
    return new_subtitle


def extract_thumbnail_main(original_video, release_video_dir, cover_title, title_font, subtitle_font, num_of_covers=1,
                           crop_height=100, isTest=False, cover_title_split_postion=0):
    # 截取3张没有汉字的截图
    frame_image_list = []
    cover_images_list = []

    print_separator(f"开始制作封面图 <<{cover_title}>>")

    cover_images_list, frame_images_list = extract_covers_and_frames(original_video, release_video_dir, 3 * num_of_covers, crop_height)
    if len(cover_images_list) != num_of_covers:
        print_separator("制作封面图超过设定时间，退出不获取了")
        return frame_image_list
    # 示例调用
    resize_images_if_needed(cover_images_list)
    # 示例调用
    cover_images_list = convert_jpeg_to_png(cover_images_list)

    for cover_path in cover_images_list:
        try:
            with Image.open(cover_path) as img:
                width, height = img.size
                if width < 1920 or height < 1080:
                    img_resized = img.resize((1920, 1080), Image.Resampling.LANCZOS)
                    img_resized.save(cover_path)
        except Exception as e:
            print(f"无法处理图像 {cover_path}。错误信息：{e}")

    for cover_path in cover_images_list:
        if is_resolution_gte_1920x1080(cover_path):
            # 先判断input_img的尺寸是不是宽高比,9:4,不是就切成9:4的宽高
            with Image.open(cover_path) as cover_image:
                # title = "测试目录测试目录测试"
                # title = os.path.basename(os.path.dirname(video_path))
                title = cover_title if cover_title else os.path.basename(os.path.dirname(original_video))

                if cover_title_split_postion > 0 and isinstance(title, str):
                    title = title[:cover_title_split_postion] + ',' + title[cover_title_split_postion:]

                title = adjust_title(title)

                subtitle = replace_subtitle("EP1-120")
                # title_color = "#FF0000"  # 红色
                # subtitle_color = "#FFFF00"  # 黄色

                title_color = "#FFFF00"  # 黄色
                subtitle_color = "#FFFF00"  # 黄色

                # title_color = "#FFFFFF"  # 白色
                # subtitle_color = "#FFFFFF"  # 白色

                font_size, subtitle_font_size = calculate_font_size(len(title))

                cover_image = write_big_title(title, subtitle, title_color,
                                              subtitle_color, title_font, subtitle_font,
                                              font_size, subtitle_font_size, cover_image)

                process_image(cover_image, cover_path)

    frame_image_list = move_images_to_release(cover_images_list, frame_images_list, release_video_dir)
    return frame_image_list


def calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, degrade):
    font_size = (base_font_size - reduction_step * degrade) * 3
    subtitle_font_size = (base_subtitle_font_size - reduction_step * degrade) * 3
    return font_size, subtitle_font_size


def calculate_font_size(char_count):
    reduction_step = 9
    base_font_size = 80
    base_subtitle_font_size = 60

    if char_count <= 5:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 0)
    elif char_count <= 7:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 0)
    elif char_count <= 10:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 3)

    elif char_count <= 11:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 1)
    elif char_count <= 12:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 1)
    elif char_count <= 13:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 1)
    elif char_count <= 14:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 2)
    elif char_count <= 15:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 3)
    elif char_count <= 16:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 4)
    elif char_count <= 17:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 4)
    elif char_count <= 18:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 4)
    elif char_count <= 20:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 5)
    else:
        font_size, subtitle_font_size = calculate_font_sizes(base_font_size, base_subtitle_font_size, reduction_step, 6)

    return font_size, subtitle_font_size


if __name__ == "__main__":
    output_dir = os.path.join('release_video', 'aa测试目录')
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, '1.mp4')
    duration = 10
    crop_height = 100
    num_frames = 3
    model_path = "ESPCN_x3.pb"

    original_video = os.path.join(os.getcwd(), 'release_video', 'aa测试目录', '1.mp4')
    release_video_dir = os.path.join(os.getcwd(), 'release_video', 'aa测试目录')

    # delete_matching_images(release_video_dir)

    fontts = [
        # ['douyin', 'DouyinSansBold.otf'],
        # ['FanThinkGrotesk', 'FanThinkGrotesk-Medium.otf'],
        # ['fengmian', 'gwkt-SC-Black.ttf'],
        # ['fengmian', 'syst-SourceHanSerifCN-Regular.otf'],
        # ['MonuTitl', 'MonuTitl-0.95CnMd.ttf'],
        # ['ShouShuTi', 'ShouShuTi.ttf'],
        # ['slideyouran', 'slideyouran_regular.ttf'],
        # ['woff', 'ChillRoundGothic_Normal.woff'],
        ['hongleibanshu', 'hongleibanshu.ttf'],
    ]

    for fooo in fontts:
        title_font = os.path.join('ziti', fooo[0], fooo[1])  # 标题
        subtitle_font = os.path.join('ziti', fooo[0], fooo[1])  # 副标题
        extract_thumbnail_main(original_video, release_video_dir, "摊牌了我的五个哥哥是大佬", title_font, subtitle_font, 1, 100, True, 0)
        # extract_thumbnail_main(original_video, release_video_dir, "目录测试目", title_font, subtitle_font, 1, 100, True,0)
        # extract_thumbnail_main(original_video, release_video_dir, "试目录测试目", title_font, subtitle_font, 1, 100, True,0)
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目", title_font, subtitle_font, 1, 100, True,0)
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目", title_font, subtitle_font, 1, 100, True,0)
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目", title_font, subtitle_font, 1, 100, True,0)
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目", title_font, subtitle_font, 1, 100, True,0)  # 10
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 11
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 12
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 13
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 14
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 15
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 16
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 17
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 18
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 19
        # extract_thumbnail_main(original_video, release_video_dir, "测试目录测试目目目目目目目目目目目目目目", title_font, subtitle_font, 1, 100, True,0)  # 20
