import concurrent.futures
import html
import os
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pysrt
import requests
import srt
from faster_whisper import WhisperModel
from googletrans import Translator
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from requests.exceptions import JSONDecodeError

from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.utils import generate_unique_key

# 设置环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 指定 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


# 设置字体路径


def transcribe_audio(audio_path, language='zh', model_size="large-v3", device="cuda", compute_type="float16"):
    base_name = os.path.splitext(audio_path)[0]
    output_srt_path = f"{base_name}_{language}.srt"

    if os.path.exists(output_srt_path):
        print(f"字幕文件已存在: {output_srt_path}")
        return output_srt_path

    print("加载模型...")
    model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
    print("开始转录音频...")

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=language,  # 如果已知语言，替换为实际语言代码
        condition_on_previous_text=False,
        vad_filter=True,  # 启用 VAD 过滤
        vad_parameters=dict(min_silence_duration_ms=200)  # 对话中可能有更短的停顿，设置为 200 毫秒
    )

    # tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3, large, distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3

    print(f"将结果写入SRT文件: {output_srt_path}")
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, start=1):
            start = segment.start
            end = segment.end
            text = segment.text

            start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
            end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"

            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

    print(f"字幕已保存到 {output_srt_path}")
    return output_srt_path


def transcribe_audio_to_srts(audio_paths, model_size="large-v3", language='zh', device="cuda", compute_type="float16"):
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [
            executor.submit(transcribe_audio, audio_path, language, model_size, device, compute_type)
            for audio_path in audio_paths
        ]
    # 收集所有的结果
    return [future.result() for future in futures]


# def transcribe_audio_to_srts(audio_paths, model_size="large-v2", device="cuda", compute_type="float16"):
#     for audio_path in audio_paths:
#         base_name = os.path.splitext(audio_path)[0]
#         output_srt_path = f"{base_name}_zh.srt"
#
#         if os.path.exists(output_srt_path):
#             print(f"字幕文件已存在: {output_srt_path}")
#             continue
#
#         print("加载模型...")
#         model = WhisperModel(model_size, device=device, compute_type=compute_type)
#         print("开始转录音频...")
#         segments, info = model.transcribe(audio_path, beam_size=5)
#
#         print(f"将结果写入SRT文件: {output_srt_path}")
#         with open(output_srt_path, "w", encoding="utf-8") as srt_file:
#             for i, segment in enumerate(segments, start=1):
#                 start = segment.start
#                 end = segment.end
#                 text = segment.text
#
#                 start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
#                 end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"
#
#                 srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
#
#         print(f"字幕已保存到 {output_srt_path}")
#     return [f"{os.path.splitext(audio_path)[0]}_zh.srt" for audio_path in audio_paths]


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
    cache_util = DiskCacheUtil()

    temp_output = os.path.splitext(output_path)[0] + "_temp.mp4"

    if os.path.exists(output_path) and cache_util.get_bool_from_cache(generate_unique_key(output_path) + "_is_added_watermark"):
        print(f"最终文件已经存在了: {output_path}")
        cache_util.close_cache()
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
                    stroke_width=2
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

        cache_util.set_bool_to_cache(generate_unique_key(output_path) + "_is_added_watermark", True)
    finally:
        if os.path.exists(temp_output):
            os.remove(temp_output)
            print(f"临时文件 {temp_output} 已删除")

        cache_util.close_cache()

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


if __name__ == '__main__':

    print("==========================================")
    audio_paths = ["./res/12miao1.mp4", "./res/12miao2.mp4"]
    zh_zimi_list = None
    # 翻译母本
    target_languages = ["zh"]
    for language in target_languages:
        zh_zimi_list = transcribe_audio_to_srts(audio_paths, language=language)
        print(zh_zimi_list)

    print("==========================================")
    #  翻译其他
    en_languages = ["en"]
    result_en = process_videos(zh_zimi_list, en_languages)
    en_video_path = []
    for en_srt_path in result_en["en"]:
        audio_path = en_srt_path.replace('_en.srt', '.mp4')
        output_video_path = audio_path.replace('.mp4', '_en.mp4')
        video_path = add_subtitles_to_video(audio_path, en_srt_path, output_video_path, subtitle_width_ratio=0.90, subtitle_y_position=220)
        en_video_path.append(video_path)
    print("生成的视频文件:", en_video_path)
    print("==========================================")
    # # 翻译其他
    target_languages = ["es", "hi", "ar", "pt", "fr", "de", "ru", "ja"]
    results = process_videos(zh_zimi_list, target_languages)
    print(results)
