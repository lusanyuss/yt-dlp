import os
import shutil
import time

import cv2
import torch
from paddleocr import PaddleOCR
from transformers import BertTokenizer, BertForMaskedLM

from yuliu.utils import print_yellow

# 初始化 PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True, show_log=False)


# 读取 SRT 文件
def read_srt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()


# 写入新的 SRT 文件
def write_srt_file(file_path, srt_content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(srt_content)


# 时间格式转换为秒数
def convert_to_seconds(time_str):
    h, m, s = map(float, time_str.split(':'))
    return h * 3600 + m * 60 + s


# 获取 OCR 结果
def get_ocr_text(frame, index, offset, bfb=10):
    height, width = frame.shape[:2]
    x_start = 0
    x_end = width
    y_start = int((75 - bfb) % 100 * height / 100)
    y_end = int((75 + bfb) % 100 * height / 100)
    # 裁剪指定区域
    roi = frame[y_start:y_end, x_start:x_end]

    # 进行 OCR 识别
    result = ocr.ocr(roi, cls=True)
    # 提取识别结果的文字
    detected_text = ''
    if result:
        for line in result:
            if line and isinstance(line, list):
                for word in line:
                    if word and isinstance(word, list) and len(word) > 1:
                        detected_text += word[1][0]
    return detected_text, roi


# 清理目录
def clear_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


# 生成偏移量列表
def generate_offsets(next_line, start_seconds, end_seconds, step=0.5):
    # if len(next_line) > 0:
    #     print(f"每个字的时间:{(end_seconds - start_seconds) / len(next_line)}")
    num = len(next_line)
    if end_seconds - start_seconds > 5:
        if 10 <= num < 20:
            step = (100 / 6) / 100
        elif 20 <= num < 30:
            step = (100 / 8) / 100
        elif 30 <= num < 40:
            step = (100 / 10) / 100
        elif 40 <= num < 50:
            step = (100 / 12) / 100
        elif num >= 50:
            step = (100 / 16) / 100

    offsets = []
    current_time = end_seconds
    while current_time > start_seconds + (end_seconds - start_seconds) * 0.24:
        if current_time == end_seconds:
            current_time -= (end_seconds - start_seconds) * step
            continue
        offsets.append(round(current_time, 1))
        current_time -= (end_seconds - start_seconds) * step
    return offsets


def are_similar(text1, text2, similarity_threshold=0.75):
    # 如果两个字符串长度不同，直接返回 False
    if len(text1) != len(text2):
        return False
    total_length = len(text1)
    # 计算相同字符的数量
    same_count = sum(1 for a, b in zip(text1, text2) if a == b)
    # 计算相同字符的比例
    similarity_ratio = same_count / total_length
    # 判断是否达到相似度阈值
    return similarity_ratio >= similarity_threshold


# 合并相等的文本
def merge_texts(texts):
    merged_text = []
    last_text = ""
    for text in reversed(texts):
        if text != last_text:
            if merged_text:
                last_element = merged_text[-1]
                if last_element in text:
                    merged_text[-1] = text
                    last_text = text
                    continue
                if text in last_element:
                    continue
                if are_similar(text, last_element, 0.75):
                    merged_text[-1] = text
                    last_text = text
                    continue
            merged_text.append(text)
        last_text = text
    return ''.join(merged_text)


# 修正字幕内容
def correct_subtitles(video_file_path, is_test=True):
    start_time_correct_subtitles = time.time()
    file_name = os.path.splitext(os.path.basename(video_file_path))[0]
    video_name = file_name.split('_')[0]
    output_image_path = os.path.dirname(video_file_path)
    output_srt_file_path = os.path.join(output_image_path, f'{video_name}_cmn_corrected.srt')

    if os.path.exists(output_srt_file_path):
        print_yellow(f"纠正文件已经存在 : {output_srt_file_path}")
        return output_srt_file_path

    tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
    model = BertForMaskedLM.from_pretrained('bert-base-chinese')
    model.eval()  # 设置为评估模式

    def compare_texts(text1, text2):
        # 函数：计算文本的平均对数似然度
        # 加载分词器和模型
        def score_text(text):
            tokenize_input = tokenizer([text], return_tensors="pt", padding=True, truncation=True, max_length=512)
            input_ids = tokenize_input["input_ids"]
            with torch.no_grad():
                outputs = model(input_ids, labels=input_ids)
            # 返回标量值
            return outputs.loss.item()

        # 为两个文本计算得分
        score1 = score_text(text1)
        score2 = score_text(text2)

        # 比较文本的得分，选择得分较低（更自然）的文本
        return text1 if score1 < score2 else text2


    srt_file_path = os.path.join(output_image_path, f'{video_name}_cmn.srt')
    srt_content = read_srt_file(srt_file_path)
    if not is_test:
        for offset in generate_offsets('', 0, 1):  # 生成一个虚拟的偏移量列表用于清理目录
            specific_output_path = os.path.join(output_image_path, f'offset_{offset}')
            clear_directory(specific_output_path)

    corrected_srt_content = []
    cap = cv2.VideoCapture(video_file_path)
    index = 1
    i = 0
    while i < len(srt_content):
        line = srt_content[i].strip()
        if line.isdigit():
            # 跳过索引行
            i += 1
            continue
        if '-->' in line:
            # 提取时间信息
            time_info = line
            next_line = srt_content[i + 1].strip()

            # 解析时间戳
            start_time = time_info.split(' --> ')[0].replace(',', '.')
            end_time = time_info.split(' --> ')[1].replace(',', '.')
            start_seconds = convert_to_seconds(start_time)
            end_seconds = convert_to_seconds(end_time)

            # 生成偏移量列表
            offsets = generate_offsets(next_line, start_seconds, end_seconds)

            # 获取视频帧并进行 OCR 识别
            detected_texts = []
            last_text = ''
            for offset in offsets:
                cap.set(cv2.CAP_PROP_POS_MSEC, offset * 1000)
                ret, frame = cap.read()
                if ret:
                    text, roi = get_ocr_text(frame, index, offset)
                    if text and text != last_text:  # 只拼接不相等的文本
                        detected_texts.append(text)  # 从右向左拼接内容
                        last_text = text
                        # 保存图片
                        roi_file = f'roi_{index}.jpg'
                        if cv2.imwrite(roi_file, roi):
                            if not is_test:
                                os.remove(roi_file)  # 删除保存的文件
                        else:
                            raise FileNotFoundError(f"文件未能成功保存: {roi_file}")

            # 合并相等的文本
            detected_text = merge_texts(detected_texts)
            print(f"Detected Text: {detected_text}")  # 调试信息

            # 修正内容
            if next_line == detected_text:
                corrected_content = next_line
            elif next_line != detected_text and len(next_line) == len(detected_text):
                corrected_content = compare_texts(detected_text, next_line)
            elif next_line in detected_text:
                corrected_content = detected_text
            elif detected_text in next_line:
                corrected_content = next_line
            else:
                corrected_content = next_line

            corrected_srt_content.append(f"{index}\n")
            corrected_srt_content.append(f"{time_info}\n")
            corrected_srt_content.append(f"{corrected_content}\n")
            corrected_srt_content.append("\n")

            index += 1
            i += 4  # 跳过每个字幕块的4行
        else:
            corrected_srt_content.append(line + '\n')
            i += 1
    # 清空

    write_srt_file(output_srt_file_path, corrected_srt_content)

    print(f"核对字幕耗时:{time.time() - start_time_correct_subtitles}")
    return output_srt_file_path


if __name__ == "__main__":
    # 文件路径

    video_file_path = 'release_video/aa测试目录big/aa测试目录big.mp4'
    corrected_srt_content = correct_subtitles(video_file_path, False)
