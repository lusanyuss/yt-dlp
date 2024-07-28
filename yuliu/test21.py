import os
from datetime import timedelta
import cv2
from paddleocr import PaddleOCR

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True, show_log=False)

def convert_to_seconds(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

def convert_to_time_str(seconds):
    td = timedelta(seconds=seconds)
    ms = int((seconds - int(seconds)) * 1000)
    time_str = str(td)
    if '.' in time_str:
        time_str, _ = time_str.split('.')
    h, m, s = time_str.split(':')
    return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03d}"

def get_ocr_text(roi):
    result = ocr.ocr(roi)
    text = ''
    if result:
        for line in result:
            if line and isinstance(line, list) and len(line) > 1 and isinstance(line[1], tuple):
                text += line[1][0]
            else:
                print(f"Unexpected OCR line format: {line}")
    print(f"OCR result: {result}")
    return text

def process_subtitle(video_path, subtitle, interval, output_image_path):
    start_seconds = convert_to_seconds(subtitle['time_range'].split(' --> ')[0])
    end_seconds = convert_to_seconds(subtitle['time_range'].split(' --> ')[1])

    cap = cv2.VideoCapture(video_path)
    ocr_texts = []
    current_time = start_seconds + interval / 1000.0

    while current_time < end_seconds:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        ret, frame = cap.read()
        if not ret:
            print(f"Frame at {current_time} seconds could not be read.")
            break

        height, width = frame.shape[:2]
        y_start = height - 450
        y_end = height - 450 + 250
        x_start = 0
        x_end = width
        roi = frame[y_start:y_end, x_start:x_end]

        screenshot_path = os.path.join(output_image_path, f'screenshot_{subtitle["index"]}_{current_time:.2f}.png')
        cv2.imwrite(screenshot_path, roi)  # 保存裁剪后的区域截图

        text = get_ocr_text(roi)
        print(f"OCR text at {current_time} seconds: '{text}'")
        if text.strip():  # 仅添加非空的文本
            ocr_texts.append(text.strip())
        current_time += interval / 1000.0

    cap.release()

    # 去重并拼接字幕内容
    new_content = []  # 用于存储去重后的字幕片段
    prev_text = ""  # 用于存储前一个片段

    for text in ocr_texts:
        if text != prev_text:
            new_content.append(text)  # 添加当前片段到 new_content 列表
            prev_text = text  # 更新 prev_text 为当前片段

    final_content = ''.join(new_content)  # 将去重后的字幕片段拼接成一个字符串
    print(f"Final content for index {subtitle['index']}: '{final_content}'")  # 调试信息，检查最终拼接结果

    subtitle['content'] = final_content  # 更新字幕内容
    return subtitle

def parse_srt(srt_file_path):
    subtitles = []
    with open(srt_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    index = None
    time_range = None
    content = []

    for line in lines:
        line = line.strip()
        if line.isdigit():
            if index is not None and time_range is not None:
                subtitles.append({
                    'index': index,
                    'time_range': time_range,
                    'content': '\n'.join(content)
                })
            index = line
            time_range = None
            content = []
        elif '-->' in line:
            time_range = line
        elif line == "":
            continue
        else:
            content.append(line)

    if index is not None and time_range is not None:
        subtitles.append({
            'index': index,
            'time_range': time_range,
            'content': '\n'.join(content)
        })

    return subtitles

def save_srt(subtitles, output_srt_file_path):
    with open(output_srt_file_path, 'w', encoding='utf-8') as file:
        for subtitle in subtitles:
            file.write(f"{subtitle['index']}\n")
            file.write(f"{subtitle['time_range']}\n")
            file.write(f"{subtitle['content']}\n\n")
    print(f"New SRT file saved successfully to {output_srt_file_path}")

def process_srt_file(video_path, srt_file_path, output_srt_file_path, interval, output_image_path):
    subtitles = parse_srt(srt_file_path)
    processed_subtitles = []
    for subtitle in subtitles:
        processed_subtitle = process_subtitle(video_path, subtitle, interval, output_image_path)
        processed_subtitles.append(processed_subtitle)
    save_srt(processed_subtitles, output_srt_file_path)

# 文件路径
video_file_path = 'release_video/aa测试目录big/aa测试目录.mp4'
srt_file_path = 'release_video/aa测试目录big/aa测试目录_cmn.srt'
output_srt_file_path = 'release_video/aa测试目录big/aa测试目录_cmn_corrected.srt'
output_image_path = 'release_video/aa测试目录'  # 指定输出目录

# 处理SRT文件
interval = 200  # 250毫秒
process_srt_file(video_file_path, srt_file_path, output_srt_file_path, interval, output_image_path)
