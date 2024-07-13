import os
import shutil
import subprocess
import time

import yt_dlp
from utils import get_file_name_with_extension, get_file_only_name, get_file_only_extension, merge_audio_and_video, separate_audio_and_video, \
    generate_md5_filename, close_chrome, get_mp4_duration, get_keyframes, find_split_points, move_file, \
    process_and_save_results, print_separator, segment_video_times, merge_videos, minutes_to_milliseconds, convert_simplified_to_traditional
from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.extract_thumbnail_main import extract_thumbnail_main


# 清除缓存逻辑
def clear_cache():
    directories_to_clear = [
        # download_cache,
        # download_directory_dir,
        # release_video,
        # mvsep_input_dir,
        # mvsep_output_dir
    ]

    print_separator("clear_cache")
    for directory in directories_to_clear:
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


def process_audio_with_mvsep_mdx23(audio_file):
    start_time = time.time()
    print(f"\n=========================处理音频文件: {os.path.basename(audio_file)}")
    shutil.copy(audio_file, mvsep_input_dir)
    intput_file_audio = os.path.join(mvsep_input_dir, get_file_name_with_extension(audio_file))

    output_file_vocals = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_vocals.wav")
    output_file_instrum = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_instrum.wav")

    if not os.path.exists(output_file_vocals):
        original_directory = os.getcwd()
        os.chdir(os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2"))
        command = ['python', 'mvsep_main.py', '--input', intput_file_audio, '--output', mvsep_output_dir]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        os.chdir(original_directory)

    if os.path.isfile(output_file_instrum):
        os.remove(output_file_instrum)

    if os.path.isfile(output_file_vocals):
        destination = shutil.copy(output_file_vocals, download_directory_dir)
        elapsed_time = time.time() - start_time
        print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")
        return os.path.abspath(destination)
    else:
        raise FileNotFoundError("输出目录中未找到 _vocals.wav 文件.")


def process_video_files(video_clips_names):
    start_time = time.time()
    processed_videos = []

    for video_file_item in video_clips_names:
        print(f"\n开始处理视频: {video_file_item}")
        # 确定 processed_video 的路径
        start_temp_time = time.time()
        processed_video = os.path.splitext(video_file_item)[0] + '_processed.mp4'
        # 如果 processed_video 已经存在，则跳过处理
        # if os.path.exists(processed_video):
        #     print(f"{processed_video} 已存在，跳过处理。")
        #     processed_videos.append(processed_video)
        #     continue
        audio_file, video_file = separate_audio_and_video(video_file_item)
        processed_audio = process_audio_with_mvsep_mdx23(audio_file)
        merge_audio_and_video(video_file, processed_audio, processed_video)
        try:
            os.remove(audio_file)
            os.remove(video_file)
            os.remove(processed_audio)
            os.remove(video_file_item)
            print("删除临时文件.")
        except OSError as e:
            print(f"删除临时文件时出错: {e}")

        print(f"成功合成无背景音乐视频: {processed_video}")
        processed_videos.append(processed_video)
        end_temp_time = time.time()
        print(f"\n结束处理{os.path.basename(video_file_item)}耗时: {end_temp_time - start_temp_time:.2f} 秒")

    end_time = time.time()
    process_video_time = end_time - start_time
    print(f"\nprocess_video_files方法耗时: {process_video_time:.2f} 秒")
    return processed_videos, process_video_time


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


def rename_file(output_video, new_name):
    new_file_name = f"{new_name}.mp4"
    file_directory = os.path.dirname(output_video)
    new_file_path = os.path.join(file_directory, new_file_name)
    os.rename(output_video, new_file_path)
    return new_file_path


def finalize_video_processing(processed_videos, output_video, release_video_dir, new_name):
    if os.path.exists(output_video):
        for file in processed_videos:
            try:
                os.remove(file)
                print(f"删除文件: {file}")
            except OSError as e:
                print(f"删除文件时出错: {e}")

        new_file_path = rename_file(output_video, new_name)
        move_file(new_file_path, release_video_dir)
        print(f"成功组合成完整视频: {os.path.join(release_video_dir, get_file_name_with_extension(new_file_path))}")


def run_main(url=None, cover_title=None, videos=None, split_time_min=15,
             is_clear_cache=False, download_only=False, sub_directory=None, video_name=None,
             number_covers=1, only_image=False):
    global download_cache_dir, download_directory_dir, release_video_dir, mvsep_input_dir, mvsep_output_dir

    print_separator("初始化路径")
    download_cache_dir = os.path.join(os.getcwd(), "download_cache")
    download_directory_dir = os.path.join(os.getcwd(), "download_directory")
    release_video_dir = os.path.join(os.getcwd(), "release_video")
    mvsep_input_dir = os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2", "input")
    mvsep_output_dir = os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2", "output")

    if sub_directory:
        download_cache_dir = os.path.join(download_cache_dir, sub_directory)
        download_directory_dir = os.path.join(download_directory_dir, sub_directory)
        release_video_dir = os.path.join(release_video_dir, sub_directory)
        mvsep_input_dir = os.path.join(mvsep_input_dir, sub_directory)
        mvsep_output_dir = os.path.join(mvsep_output_dir, sub_directory)

    ensure_directory_exists(download_cache_dir)
    ensure_directory_exists(download_directory_dir)
    ensure_directory_exists(release_video_dir)
    ensure_directory_exists(mvsep_input_dir)
    ensure_directory_exists(mvsep_output_dir)

    if sub_directory and sub_directory == 'mytest':
        clear_cache()
    if is_clear_cache:
        clear_cache()

    split_time_ms = minutes_to_milliseconds(split_time_min)
    cache_util = DiskCacheUtil()
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
        original_video, download_time = download_video(url, video_name)
        if download_only:
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

    # extract_first_5_minutes(original_video, release_video_dir)
    extract_thumbnail_main(original_video, release_video_dir, cover_title, number_covers, 100)

    if only_image:
        return

    # print_separator("输入 'y' 继续: ")
    # user_input = input("输入 'y' 继续: ")
    # if user_input.lower() == 'y':
    #     pass
    # else:
    #     print("操作已取消")
    #     sys.exit()

    print_separator("1.处理视频,切成小块视频,进行处理")
    output_pattern = os.path.join(os.path.dirname(original_video), 'out_times_%02d.mp4')
    merged_video_name = f"{get_file_only_name(original_video)}_mex23{get_file_only_extension(original_video)}"
    merged_video_path = os.path.join(os.path.dirname(original_video), merged_video_name)
    print(f"\n原始视频路径: {original_video}")
    video_duration = get_mp4_duration(original_video)
    print(f"\n原始视频时长: {video_duration}")
    keyframe_times = get_keyframes(original_video, split_time_ms)
    split_points = find_split_points(keyframe_times, split_time_ms)
    video_clips = segment_video_times(original_video, split_points, output_pattern)
    print(f"\n原始视频已拆分成{len(video_clips)}份,将逐一进行音频处理")

    print_separator("2.对视频人声分离")
    processed_videos, process_video_time = process_video_files(video_clips)
    output_path = merge_videos(processed_videos, merged_video_path)

    process_and_save_results(original_video, download_time, process_video_time, result_file_name)
    finalize_video_processing(processed_videos, output_path, release_video_dir, sub_directory)

    print(f"""

《{convert_simplified_to_traditional(sub_directory)}》【高清完結合集】

歡迎訂閱《爽剧风暴》的頻道哦 https://www.youtube.com/@SJFengBao?sub_confirmation=1
正版授權短劇，感謝大家支持 ！

    """
          )
