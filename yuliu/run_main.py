import os
import re
import shutil
import time

from torchvision.datasets.utils import calculate_md5

import yt_dlp
from utils import get_file_name_with_extension, get_file_only_name, get_file_only_extension, generate_md5_filename, close_chrome, get_mp4_duration, \
    find_split_points, \
    process_and_save_results, print_separator, segment_video_times, merge_videos, minutes_to_milliseconds, convert_simplified_to_traditional, \
    separate_audio_and_video_list, merge_audio_and_video_list, generate_unique_key
from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.extract_thumbnail_main import extract_thumbnail_main
from yuliu.keyframe_extractor import KeyFrameExtractor
from yuliu.transcribe_video import transcribe_audio_to_srts, process_videos, generate_video_with_subtitles


def clear_directory_contents(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'删除 {file_path} 时出错: {e}')
        print(f'已清空目录: {directory}')
    else:
        print(f'目录不存在: {directory}')


# 清除缓存逻辑
def clear_cache():
    directories_to_clear = [
        # download_cache_dir,
        download_directory_dir,
        release_video_dir,
        mvsep_input_dir,
        # mvsep_output_dir
    ]
    print_separator("clear_cache")
    for directory in directories_to_clear:
        clear_directory_contents(directory)


def process_audio_with_mvsep_mdx23_list(audio_files):
    start_time = time.time()
    print(f"\n========================================处理音频文件(去除背景音乐)")
    # 输出文件列表定义
    # 输出文件定义
    output_file_vocals_list = []
    output_file_instrum_list = []
    destination_vocals_list = []
    for audio_file in audio_files:
        output_file_vocals = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_vocals.wav")
        output_file_instrum = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_instrum.wav")
        output_file_vocals_list.append(output_file_vocals)
        output_file_instrum_list.append(output_file_instrum)

    # 输入文件处理
    clear_directory_contents(mvsep_input_dir)
    for audio_file in audio_files:
        shutil.copy(audio_file, mvsep_input_dir)

    if not all(os.path.exists(file) for file in output_file_vocals_list):
        print(f"并不所有文件都存在。清空目录{mvsep_output_dir}")
        clear_directory_contents(mvsep_output_dir)
        try:
            original_directory = os.getcwd()
            os.chdir(os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2"))
            command = ['python', 'mvsep_main.py', '--input', mvsep_input_dir, '--output', mvsep_output_dir]
            command_str = ' '.join(command)
            print(command_str)
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            os.chdir(original_directory)
        except Exception as e:
            print(f"处理音频文件时发生错误: {e}")
    else:
        print("所有文件都存在。")
    elapsed_time = time.time() - start_time
    print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")

    for output_file_vocals in output_file_vocals_list:
        if os.path.exists(output_file_vocals):
            destination = shutil.copy(output_file_vocals, download_directory_dir)
            destination_vocals_list.append(destination)
    return destination_vocals_list, output_file_instrum_list


def are_files_same(audio_files, output_dir):
    mvsep_files = [os.path.join(audio_files, file) for file in os.listdir(audio_files) if os.path.isfile(os.path.join(audio_files, file))]

    # 比较文件数量
    if len(audio_files) != len(mvsep_files):
        return False

    # 比较文件名
    audio_files_names = sorted([os.path.basename(file) for file in audio_files])
    mvsep_files_names = sorted([os.path.basename(file) for file in mvsep_files])

    if audio_files_names != mvsep_files_names:
        return False

    # 比较文件 MD5
    for audio_file in audio_files:
        corresponding_mvsep_file = os.path.join(output_dir, os.path.basename(audio_file))
        if not os.path.exists(corresponding_mvsep_file):
            return False
        if calculate_md5(audio_file) != calculate_md5(corresponding_mvsep_file):
            return False

    return True


def process_video_files_list(video_origin_clips):
    start_time = time.time()
    video_dest_list = []
    # 多线程分割视频
    audio_origin_list, video_origin_list = separate_audio_and_video_list(video_origin_clips)
    # 单线程去除视频背景音乐
    audio_vocals_list, audio_instrum_list = process_audio_with_mvsep_mdx23_list(audio_origin_list)

    for index, video_file_item in enumerate(video_origin_clips, start=1):
        video_dest = os.path.splitext(video_file_item)[0] + '_processed.mp4'
        video_dest_list.append(video_dest)
    video_dest_list = merge_audio_and_video_list(video_origin_list, audio_vocals_list, video_dest_list)
    end_time = time.time()
    process_video_time = end_time - start_time
    return video_dest_list, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, audio_instrum_list, process_video_time


def get_video_list(result):
    video_list = []
    for entry in result['entries']:
        video_id = entry['id']
        video_ext = entry['ext']
        video_name = f"{video_id}.{video_ext}"
        video_list.append(os.path.join(download_cache_dir, video_name))
    return video_list


def add_timestamp_to_filename(file_path):
    # 提取当前时间戳
    timestamp = int(time.time())
    # 获取文件路径和扩展名
    base_path, file_extension = os.path.splitext(file_path)
    # 创建新的文件路径，带有时间戳
    new_file_path = f"{base_path}_{timestamp}{file_extension}"
    # 重命名文件
    os.rename(file_path, new_file_path)


def download_video(url, video_name):
    def video_exists(video_path):
        return os.path.isfile(video_path)

    def process_playlist(result):
        print("处理多视频播放列表")
        id = result['id']
        merged_video = f"{id}.{result['entries'][0]['ext']}"
        merged_video_path = os.path.join(download_cache_dir, merged_video)
        if not video_exists(merged_video_path):
            video_list = get_video_list(result)
            merge_videos(video_list, merged_video_path)
        add_timestamp_to_filename(merged_video_path)
        shutil.copy(merged_video_path, download_directory_dir)
        return os.path.join(download_directory_dir, merged_video)

    def process_single_video(video_path):
        print("处理单个视频")
        if video_exists(video_path):
            print(f"视频已经存在（缓存）: {video_path}")
            shutil.copy(video_path, download_directory_dir)
        if not video_name:
            add_timestamp_to_filename(video_path)
        return os.path.join(download_directory_dir, get_file_only_name(video_path))

    close_chrome()

    video_path = os.path.join(download_cache_dir, '%(id)s.%(ext)s')
    if video_name:
        video_path = os.path.join(download_cache_dir, f"{video_name}.%(ext)s")

    ydl_opts = {
        'outtmpl': video_path,
        'format': 'bv*+ba/b',
        'ignoreerrors': True,
        'cookiesfrombrowser': ('chrome', None),
        'progress_hooks': [my_hook],
    }

    start_time = time.time()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        result = ydl.extract_info(url, download=False)

        if 'entries' in result:
            video_path = process_playlist(result)
        else:
            video_path = process_single_video(video_path)

    end_time = time.time()
    download_time = end_time - start_time
    return video_path, download_time


def my_hook(d):
    if d['status'] == 'finished':
        print(f"下载完成: {d['filename']}")


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"删除文件: {file_path}")
    except OSError as e:
        print(f"删除文件时出错: {e}")


def finalize_video_processing(video_dest_result, release_video_dir, sub_directory):
    if os.path.exists(video_dest_result):
        # 加水印
        result_video = add_watermark_to_video(video_dest_result)
        print(f"成功组合成完整视频: {os.path.join(release_video_dir, get_file_name_with_extension(result_video))}")

        # 保存标题和描述

        content = f"""

请根据以下标题生成适合搜索和吸引点击的整个标题和说明描述，使用中文繁体字，主标题和副标题写一起组合成整个标题,用|分开, 在说明描述中包含用 | 分割的相关标签。整个标题需要便于搜索，足够接地气，容易出现在搜索列表中，并且富有吸引力，让人感兴趣，使人立即点击观看。说明描述的第一个段落一定是：

歡迎訂閱《爽剧风暴》的頻道哦 https://www.youtube.com/@SJFengBao?sub_confirmation=1
正版授權短劇，感謝大家支持！

主标题：\n《{convert_simplified_to_traditional(sub_directory)}》【高清完結合集】

        """
        video_dest_result = f"{release_video_dir}/{convert_simplified_to_traditional(sub_directory)}.txt"
        with open(video_dest_result, 'w', encoding='utf-8') as file:
            file.write(content)


import subprocess


# ffmpeg -i "release_video/aa测试目录/aa测试目录.mp4" -vf "drawtext=fontfile='ziti/fengmian/gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "release_video/aa测试目录/temp_output.mp4"
# ffmpeg -i "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录.mp4" -vf "drawtext=fontfile='C:\yuliu\workspace\yt-dlp\yuliu\ziti\fengmian\gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\temp_output.mp4"
# ffmpeg -i "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录.mp4" -vf "drawtext=fontfile='C:\yuliu\workspace\yt-dlp\yuliu\ziti\fengmian\gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\temp_output.mp4"

def add_watermark_to_video(video_path):
    cache_util = DiskCacheUtil()
    unique_key = None

    if os.path.exists(video_path):
        unique_key = generate_unique_key(video_path) + "_is_added_watermark"
        if cache_util.get_bool_from_cache(unique_key):
            print(f"文件已存在且已添加水印: {video_path}")
            cache_util.close_cache()
            return video_path

    print_separator("添加水印-开始 " + video_path)
    font_file = 'ziti/fengmian/gwkt-SC-Black.ttf'  # 使用相对路径
    text = "爽剧风暴"
    temp_output = os.path.join(os.path.dirname(video_path), "temp_output.mp4").replace("\\", "/")

    # 获取视频时长
    video_duration_ms = get_mp4_duration(video_path)
    video_duration_s = video_duration_ms / 1000  # 将毫秒转换为秒
    # 计算分钟数
    minutes_needed = video_duration_s / 60 / 4.3

    # 构建命令字符串，使用相对路径，并确保格式正确
    command = (
        f'ffmpeg -i "{video_path}" -vf "drawtext=fontfile=\'{font_file}\':text=\'{text}\':'
        f'fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable=\'between(t,0,{video_duration_s})\'" '
        f'-c:a copy -y "{temp_output}"'
    )

    # 打印命令以便手动检查
    print("Running command: \n", command)
    print(f"请耐心等待...大概需要 {minutes_needed:.2f} 分钟")

    try:
        # 使用 shell=True 执行命令字符串
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        result.check_returncode()  # 检查命令是否成功
        os.replace(temp_output, video_path)  # Replace the original video with the new one
        unique_key = generate_unique_key(video_path) + "_is_added_watermark"
        cache_util.set_bool_to_cache(unique_key, True)
        print_separator("添加水印-成功")
    except Exception as e:
        print(f"Error occurred: {e}")
        if os.path.exists(temp_output):
            os.remove(temp_output)  # Remove the temporary output file if it exists
        return video_path
    finally:
        cache_util.close_cache()

    return video_path


def get_dir(base_dir, sub_directory=None):
    dir_path = os.path.join(os.getcwd(), base_dir)
    if sub_directory:
        dir_path = os.path.join(dir_path, sub_directory)
    return dir_path


def get_sorted_vocals_wav_files(directory):
    pattern = re.compile(r'out_times_(\d+)_audio_vocals\.wav')
    files = [file for file in os.listdir(directory) if pattern.match(file)]
    files.sort(key=lambda x: int(pattern.search(x).group(1)))
    return [os.path.join(directory, file) for file in files]


def run_main(url=None,
             videos=None,

             cover_title=None,
             split_time_min=15,
             is_clear_cache=False,

             is_only_download=False,
             sub_directory=None,
             video_download_name=None,
             is_get_video=True,
             num_of_covers=1,
             is_get_cover=False):
    global download_cache_dir, download_directory_dir, release_video_dir, mvsep_input_dir, mvsep_output_dir

    print_separator("初始化路径")

    download_cache_dir = get_dir("download_cache", sub_directory)
    download_directory_dir = get_dir("download_directory", sub_directory)
    release_video_dir = get_dir("release_video", sub_directory)
    mvsep_input_dir = get_dir(os.path.join("MVSEP-MDX23-Colab_v2", "input"), sub_directory)
    mvsep_output_dir = get_dir(os.path.join("MVSEP-MDX23-Colab_v2", "output"), sub_directory)
    ensure_directory_exists(download_cache_dir)
    ensure_directory_exists(download_directory_dir)
    ensure_directory_exists(release_video_dir)
    ensure_directory_exists(mvsep_input_dir)
    ensure_directory_exists(mvsep_output_dir)
    dest_video_path = os.path.join(release_video_dir, f"{sub_directory}.mp4")

    cache_util = DiskCacheUtil()

    split_time_ms = minutes_to_milliseconds(split_time_min)
    previous_split_time = cache_util.get_from_cache("split_time_ms", 900 * 1000)
    print(f"上次切割时间单位:{previous_split_time}毫秒")
    print(f"当前切割时间单位:{split_time_ms}毫秒")
    if previous_split_time is None or previous_split_time != split_time_ms:
        print_separator("更新切割时间")
        clear_cache()
        cache_util.set_to_cache("split_time_ms", split_time_ms)

    result_file_name = "video_processing_results.txt"

    download_time = 0
    if url:
        print_separator("下载视频")
        original_video, download_time = download_video(url, video_download_name)
        if is_only_download:
            print("Download only mode is enabled. Exiting the program after download.")
            exit()
    else:
        if len(videos) > 1:
            print_separator("合并视频")
            original_video = os.path.join(download_directory_dir, generate_md5_filename(videos))
            if not os.path.exists(original_video):
                original_video = merge_videos(videos, original_video)
        else:
            print_separator("复制视频文件到下载目录")
            target_path = os.path.join(download_directory_dir, os.path.basename(videos[0]))
            shutil.copy(videos[0], target_path)
            original_video = target_path

    frame_image_list = []
    if is_get_cover:
        # 记录开始时间
        start_time = time.time()
        title_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 标题
        subtitle_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 副标题
        frame_image_list = extract_thumbnail_main(original_video, release_video_dir,
                                                  cover_title, title_font, subtitle_font,
                                                  num_of_covers=num_of_covers,
                                                  crop_height=100, isTest=False)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"获取{num_of_covers}张图片时间: {elapsed_time:.2f} 秒, 平均每张: {elapsed_time / num_of_covers:.2f} 秒")

    if is_get_video:
        # if os.path.exists(dest_video_path):
        #     unique_key = generate_unique_key(dest_video_path) + "_is_added_watermark"
        #     if cache_util.get_bool_from_cache(unique_key):
        #         print(f"文件已存在且已添加水印: {dest_video_path}")
        #         # print(f"{get_file_name_with_extension(dest_video_path)}已存在，不需要再处理了,直接返回")
        #         # target_languages = ["es", "hi", "ar", "pt", "fr", "de", "ru", "ja"]
        #         # audio_paths = get_sorted_vocals_wav_files(download_directory_dir)
        #         # output_zh_srt_path = transcribe_audio_to_srts(audio_paths)
        #         # subtitle_paths, video_path = process_videos(dest_video_path, ["en"])
        #         # print_separator()
        #         cache_util.close_cache()
        #         return

        print_separator(f"1.处理视频,切成小块视频,进行处理({cover_title})")
        output_pattern = os.path.join(os.path.dirname(original_video), 'out_times_%02d.mp4')
        video_dest_result = os.path.join(release_video_dir, f"{sub_directory}{get_file_only_extension(original_video)}")
        print(f"\n原始视频路径: {original_video}")
        video_duration = get_mp4_duration(original_video)
        print(f"\n原始视频时长: {video_duration}")
        keyframeextractor = KeyFrameExtractor(original_video, cache_util)
        keyframe_times = keyframeextractor.extract_keyframes()
        split_points = find_split_points(keyframe_times, split_time_ms)
        video_clips = segment_video_times(original_video, split_points, output_pattern)
        print(f"\n原始视频已拆分成{len(video_clips)}份,将逐一进行音频处理")

        print_separator(f"2.对视频人声分离({cover_title})")

        (video_dest_list, audio_origin_list,
         video_origin_list, audio_vocals_list,
         video_origin_clips, audio_instrum_list,
         process_video_time) = process_video_files_list(video_clips)

        print("==========================================")
        # 翻译zh-CN字幕母本
        zh_cn_zimi_list = None
        target_languages = ["zh"]
        for language in target_languages:
            zh_cn_zimi_list = transcribe_audio_to_srts(video_dest_list, language=language)
            print(zh_cn_zimi_list)

        #  翻译en字幕
        en_languages = ["en"]
        result_en_srt = process_videos(zh_cn_zimi_list, en_languages)
        en_video_path = []
        #  en字幕加到视频上
        print("英文视频字幕顺序:", result_en_srt["en"])
        for en_srt_path in result_en_srt["en"]:
            audio_path = en_srt_path.replace('_en.srt', '.mp4')
            output_video_path = audio_path.replace('.mp4', '_en.mp4')
            print("en_srt_path:", en_srt_path)
            print("audio_path:", audio_path)
            print("output_video_path:", output_video_path)

            video_path = generate_video_with_subtitles(audio_path, en_srt_path, output_video_path,
                                                       subtitle_width_ratio=0.90, subtitle_y_position=220)
            en_video_path.append(video_path)
        print("生成的视频文件:", en_video_path)

        # target_languages = ["es", "hi", "ar", "pt", "fr", "de", "ru", "ja"]
        # results_other_srt = process_videos(zh_cn_zimi_list, target_languages)
        # print(f"其他地区字幕翻译：{results_other_srt}")

        #  目标视频变成有因为的视频，字幕加到视频上
        delete_files_by_list(video_dest_list)
        video_dest_list = en_video_path
        # 合成目标视频
        video_dest_result = merge_videos(video_dest_list, video_dest_result)

        process_and_save_results(original_video, download_time, process_video_time, result_file_name, sub_directory)
        finalize_video_processing(video_dest_result, release_video_dir, sub_directory)
        # delete_files(audio_file_list, video_file_list, audio_vocals_list, video_file_item_list, processed_audio_instrum_list, frame_image_list)
        # delete_files(audio_origin_list, video_origin_list, video_origin_clips, audio_instrum_list, frame_image_list)
        cache_util.close_cache()


def delete_files_by_list(frame_image_list):
    for file in frame_image_list:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except OSError:
            print(f"Failed to delete: {file}")


def delete_files(audio_file_list=[], video_file_list=[], audio_vocals_list=[], video_file_item_list=[], audio_instrum_list=[], frame_image_list=[]):
    all_files = audio_file_list + video_file_list + audio_vocals_list + video_file_item_list + audio_instrum_list + frame_image_list
    for file in all_files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except OSError:
            print(f"Failed to delete: {file}")
