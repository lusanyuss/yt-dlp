import concurrent.futures
import html
import logging
import os
import textwrap
import threading
import time
from threading import Lock

import pysrt
import requests
import srt
from faster_whisper import WhisperModel  # 假设这是一个已安装的库
from googletrans import Translator
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from requests.exceptions import JSONDecodeError

from yuliu.transcribe_srt import iso639_3_to_2
from yuliu.utils import has_zimu_suffix, print_yellow, process_srt, get_path_without_suffix

# 设置环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 指定 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def transcribe_audio_to_srt(audio_path, language='zh', model_size="large-v2", device="cuda", compute_type="float16", sub_directory=""):
    base, ext = os.path.splitext(audio_path)
    base_name = get_path_without_suffix(base)
    srt_path = f"{base_name}_{language}.srt"
    temp_srt_path = f"{base_name}_{language}_temp.srt"

    if os.path.exists(temp_srt_path):
        os.remove(temp_srt_path)
    if os.path.exists(srt_path):
        print_yellow(f"字幕文件已存在: {srt_path}")
        return srt_path

    print("加载模型...")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

    try:
        start_time1 = time.time()
        model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            language=iso639_3_to_2(language),
            condition_on_previous_text=False,
            vad_filter=False,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        print(f"开始转录音频: {time.time() - start_time1:.2f} 秒")
        print(f"将结果写入临时SRT文件: {temp_srt_path}")

        start_time2 = time.time()
        with open(temp_srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments, start=1):
                start = segment.start
                end = segment.end
                text = segment.text

                start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
                end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"

                srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        print(f"将结果写入临时SRT文件: {time.time() - start_time2:.2f} 秒")
        # 去掉大模型添加的前尾30秒加密信息
        # temp_srt_path = process_srt(temp_srt_path)
        os.replace(temp_srt_path, srt_path)
        print(f"字幕已保存到 {srt_path}")
    except Exception as e:
        if os.path.exists(temp_srt_path):
            os.remove(temp_srt_path)
        print(f"发生异常: {str(e)}")
        raise e
    return srt_path


def translate_text_bygoogle(text, source_lang='zh', target_lang='en'):
    translator = Translator()
    # 翻译文本
    try:
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        print(f"发生错误: {e}")
        return None


def translate_text(text, source_lang='zh', target_lang='en'):
    url = f"https://findmyip.net/api/translate.php?text={text}&source_lang={source_lang}&target_lang={target_lang}"
    response = requests.get(url)
    try:
        data = response.json()
        if response.status_code == 200:
            if data['code'] == 200:
                translation = data['data']['translate_result']
                translation = html.unescape(translation)  # 处理HTML编码
                return translation
            elif data['code'] == 400:
                return data['error']
            else:
                return "内部接口错误，请联系开发者"
        else:
            return "内部接口错误，请联系开发者"
    except JSONDecodeError as e:
        return f"JSON decoding error: {e}"
    except requests.RequestException as e:
        return f"Request error: {e}"


def translate_srt(srt_path, translated_srt_path, target_lang='en'):
    print(f"\n=========翻译字幕: {translated_srt_path}\n")

    if os.path.exists(translated_srt_path):
        print(f"==========翻译后的字幕文件已存在: {translated_srt_path}")
        return translated_srt_path

    with open(srt_path, 'r', encoding='utf-8') as file:
        subtitles = list(srt.parse(file.read()))

    translated_subtitles = [None] * len(subtitles)
    lock = Lock()

    def translate_and_save(index, subtitle):
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            translated_text = translate_text_bygoogle(subtitle.content, source_lang='zh-CN', target_lang=target_lang)
            if translated_text is not None:
                break
            print(f"翻译失败，重试 {attempt + 1}/{max_retries} 次...")
            time.sleep(retry_delay)
        else:
            print(f"删除错误文件: {translated_srt_path} , 无法翻译字幕 {subtitle.content}")
            os.remove(translated_srt_path)
            exit(1)

        print(f"翻译: {subtitle.content}  --->  {translated_text}")

        with lock:
            translated_subtitles[index] = srt.Subtitle(index=subtitle.index, start=subtitle.start, end=subtitle.end, content=translated_text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = []
        for i, subtitle in enumerate(subtitles):
            futures.append(executor.submit(translate_and_save, i, subtitle))
        for future in concurrent.futures.as_completed(futures):
            future.result()  # 确保所有任务都完成

    with open(translated_srt_path, 'w', encoding='utf-8') as file:
        file.write(srt.compose(translated_subtitles))

    print(f"翻译后的字幕已保存到 {translated_srt_path}")
    return translated_srt_path


def add_subtitles_to_video(video_path, srt_path, output_path, subtitle_width_ratio=0.80, subtitle_y_position=220):
    temp_output = os.path.splitext(output_path)[0] + "_temp.mp4"

    if os.path.exists(output_path) and has_zimu_suffix(output_path):
        print(f"已经加过字幕了")
        return output_path

    try:
        print(f"读取视频文件: {video_path}")
        video = VideoFileClip(video_path)
        video_width, video_height = video.size
        print(f"视频尺寸: {video_width}x{video_height}")

        print(f"读取字幕文件: {srt_path}")
        with open(srt_path, 'r', encoding='utf-8') as file:
            subtitles = list(srt.parse(file.read()))

        clips = []

        subtitle_width = video_width * subtitle_width_ratio
        max_chars_per_line = int(subtitle_width // 20)

        font_path = "Impact"  # 使用系统中的 Impact 字体
        # font_path = r"C:\Windows\Fonts\arialbd.ttf"
        for subtitle in subtitles:
            start_time = subtitle.start.total_seconds()
            end_time = subtitle.end.total_seconds()
            text = subtitle.content

            wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

            try:
                txt_clip = TextClip(
                    wrapped_text,
                    fontsize=48,
                    color='yellow',
                    font=font_path,
                    size=(subtitle_width, 150),  # 设置固定高度为 150
                    stroke_color='black',  # 添加黑色边框
                    stroke_width=2,
                    print_cmd=True
                )
                txt_clip = txt_clip.on_color(color=(0, 0, 0), col_opacity=0)
                txt_clip = txt_clip.set_position(('center', video_height - subtitle_y_position))
                txt_clip = txt_clip.set_start(start_time)
                txt_clip = txt_clip.set_duration(end_time - start_time)

                print(f"创建字幕: '{wrapped_text}' 为： {video_path}")

                clips.append(txt_clip)
            except Exception as e:
                print(f"创建字幕时出错: {e}")

        print(f"总共创建了 {len(clips)} 条字幕")

        final_clip = CompositeVideoClip([video] + clips, size=video.size)

        print(f"开始写入最终视频文件: {temp_output}")
        final_clip.write_videofile(temp_output, codec="libx264", fps=video.fps)
        print("视频文件写入完成")

        os.replace(temp_output, output_path)  # 将临时文件重命名为最终输出文件
        print(f"临时文件重命名为: {output_path}")
    finally:
        if os.path.exists(temp_output):
            os.remove(temp_output)
            print(f"临时文件 {temp_output} 已删除")

    return output_path


def generate_subtitles(zh_zimu, language):
    # 将音频转录为中文SRT字幕文件
    dest_zimu = zh_zimu.replace('_zh.srt', f'_{language}.srt')
    translated_srt_path = translate_srt(zh_zimu, dest_zimu, target_lang=language)
    return translated_srt_path


def wait_for_input(prompt, timeout):
    """等待用户输入，超时则返回空字符串"""

    def inner():
        nonlocal user_input
        user_input = input(prompt)

    user_input = ""
    thread = threading.Thread(target=inner)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    return user_input


def concatenate_srt_files(srt_list):
    """拼接多个SRT文件的内容并调整索引和时间戳"""
    concatenated_subs = pysrt.SubRipFile()
    total_duration = pysrt.SubRipTime(0, 0, 0, 0)
    current_index = 1

    for srt_file in srt_list:
        subs = pysrt.open(srt_file)
        for sub in subs:
            # 调整时间戳
            sub.start += total_duration
            sub.end += total_duration
            # 调整索引
            sub.index = current_index
            current_index += 1
            # 添加到最终的SRT文件
            concatenated_subs.append(sub)
        # 更新总持续时间
        total_duration += subs[-1].end

    return concatenated_subs


def process_videos(zh_zimi_list, target_languages):
    results = {}
    for language in target_languages:
        results[language] = []
        for zh_zimu in zh_zimi_list:
            translated_srt_path = generate_subtitles(zh_zimu, language)
            results[language].append(translated_srt_path)
    return results


def process_videos_zh(audio_vocals_list):
    results = []

    for audio_vocals in audio_vocals_list:
        zh_language = 'zh'
        # 第一步：生成zh字幕
        zh_subtitle_path = generate_subtitles(audio_vocals, [zh_language])[0]
        print("生成的中文字幕文件:", zh_subtitle_path)
        results.append(zh_subtitle_path)

    return results
