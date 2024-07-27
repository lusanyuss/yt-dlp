import os
import shutil
import cv2
from paddleocr import PaddleOCR

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
def get_ocr_text(frame, index, offset, jianju=450):
    height, width = frame.shape[:2]
    y_start = height - jianju
    y_end = height - jianju + 250
    x_start = 0
    x_end = width

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


# 修正字幕内容
def correct_subtitles(video_file_path, srt_content, output_path, offsets, is_test):
    if not is_test:
        for offset in offsets:
            specific_output_path = os.path.join(output_path, f'offset_{offset}')
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
            end_seconds = convert_to_seconds(end_time) - min(offsets)  # 从最小偏移量开始

            # 获取视频帧并进行 OCR 识别
            detected_text = ''
            for offset in offsets:
                cap.set(cv2.CAP_PROP_POS_MSEC, (end_seconds - offset) * 1000)
                ret, frame = cap.read()
                if ret:
                    detected_text, roi = get_ocr_text(frame, index, offset)
                    if detected_text:  # 如果检测到文字则保存图片并退出循环
                        specific_output_path = os.path.join(output_path, f'offset_{offset}')
                        os.makedirs(specific_output_path, exist_ok=True)
                        roi_file = f'roi_{index}.jpg'
                        if cv2.imwrite(roi_file, roi):
                            full_roi_file_path = os.path.join(specific_output_path, roi_file)
                            os.replace(roi_file, full_roi_file_path)
                            print(f"Saving ROI to: {full_roi_file_path}")  # 打印路径信息
                        else:
                            raise FileNotFoundError(f"文件未能成功保存: {roi_file}")
                        break

            # 修正内容
            corrected_content = next_line if next_line == detected_text else (detected_text if detected_text else next_line)

            corrected_srt_content.append(f"{index}\n")
            corrected_srt_content.append(f"{time_info}\n")
            corrected_srt_content.append(f"{corrected_content}\n")
            corrected_srt_content.append("\n")

            index += 1
            i += 4  # 跳过每个字幕块的4行
        else:
            corrected_srt_content.append(line + '\n')
            i += 1

    return corrected_srt_content


if __name__ == "__main__":
    # 文件路径
    video_file_path = 'release_video/aa测试目录/aa测试目录.mp4'
    srt_file_path = 'release_video/aa测试目录/aa测试目录_cmn.srt'
    output_srt_file_path = 'release_video/aa测试目录/aa测试目录_cmn_corrected.srt'
    output_image_path = 'release_video/aa测试目录'  # 指定输出目录
    offsets = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]  # 偏移量配置
    is_test = False  # 设置是否为测试模式

    srt_content = read_srt_file(srt_file_path)
    corrected_srt_content = correct_subtitles(video_file_path, srt_content, output_image_path, offsets, is_test)
    write_srt_file(output_srt_file_path, corrected_srt_content)
