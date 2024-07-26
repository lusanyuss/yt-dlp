import os
import re
import shutil
import subprocess
import time

from torchvision.datasets.utils import calculate_md5

import yt_dlp
import yuliu.transcribe_srt
from utils import get_file_only_name, get_file_only_extension, generate_md5_filename, close_chrome, get_mp4_duration, \
    find_split_points, \
    process_and_save_results, print_separator, segment_video_times, merge_videos, minutes_to_milliseconds, convert_simplified_to_traditional, \
    separate_audio_and_video_list, merge_audio_and_video_list, has_zimu_suffix, CommandExecutor
from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.extract_thumbnail_main import extract_thumbnail_main
from yuliu.keyframe_extractor import KeyFrameExtractor
from yuliu.transcribe_video import transcribe_audio_to_srt
from yuliu.zimu_utils import add_zimu_shuiyin_to_video

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


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
    destination_vocals_list = []

    for audio_file in audio_files:
        output_file_vocals = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_vocals.wav")
        output_file_vocals_list.append(output_file_vocals)

    # 输入文件处理
    clear_directory_contents(mvsep_input_dir)
    for audio_file in audio_files:
        shutil.copy(audio_file, mvsep_input_dir)

    if not all(os.path.exists(file) for file in output_file_vocals_list):
        print(f"并不所有文件都存在。清空目录{mvsep_output_dir}")
        clear_directory_contents(mvsep_output_dir)
        try:
            mvsep_main = os.path.join(mvsep_base_dir, 'mvsep_main.py')
            command = ['python', f'{mvsep_main}', '--input', mvsep_input_dir, '--output', mvsep_output_dir]
            print(' '.join(command))
            CommandExecutor.run_command(command)
            # subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        except Exception as e:
            print(f"处理音频文件时发生错误: {e}")
    else:
        print("所有文件都存在。")
    elapsed_time = time.time() - start_time
    print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")

    for output_file_vocals in output_file_vocals_list:
        if os.path.exists(output_file_vocals):
            destination = shutil.copy(output_file_vocals, release_video_dir)
            destination_vocals_list.append(destination)
    return destination_vocals_list


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


def check_files_exist(file_list):
    # 检查每个文件是否存在
    for file in file_list:
        if not os.path.isfile(file):
            # 如果有任何文件不存在，返回空数组
            return []
    # 如果所有文件都存在，返回原始数组
    return file_list


def process_video_files_list(video_origin_clips):
    start_time = time.time()
    video_dest_list = []
    for index, video_file_item in enumerate(video_origin_clips, start=1):
        video_dest_list.append(os.path.splitext(video_file_item)[0] + '_processed.mp4')

    if all(os.path.isfile(file) for file in video_dest_list):
        process_video_time = time.time() - start_time
        return video_dest_list, [], [], [], [], process_video_time
    else:
        # 多线程分割视频
        audio_origin_list, video_origin_list = separate_audio_and_video_list(video_origin_clips)
        # 单线程去除视频背景音乐
        audio_vocals_list = process_audio_with_mvsep_mdx23_list(audio_origin_list)

        video_dest_list = merge_audio_and_video_list(video_origin_list, audio_vocals_list, video_dest_list)

        process_video_time = time.time() - start_time
        return video_dest_list, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, process_video_time


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
        shutil.copy(merged_video_path, release_video_dir)
        return os.path.join(release_video_dir, merged_video)

    def process_single_video(video_path):
        print("处理单个视频")
        if video_exists(video_path):
            print(f"视频已经存在（缓存）: {video_path}")
            shutil.copy(video_path, release_video_dir)
        if not video_name:
            add_timestamp_to_filename(video_path)
        return os.path.join(release_video_dir, get_file_only_name(video_path))

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


def generate_video_metadata(release_video_dir, sub_directory):
    # 创建目录（如果不存在）
    os.makedirs(release_video_dir, exist_ok=True)

    # 转换子目录名称为繁体字
    traditional_sub_directory = convert_simplified_to_traditional(sub_directory)

    # 文件路径
    video_dest_result = f"{release_video_dir}/{traditional_sub_directory}.txt"

    # 检查文件是否已存在并包含内容
    if os.path.exists(video_dest_result) and os.path.getsize(video_dest_result) > 0:
        print(f"文件 {video_dest_result} 已存在且包含内容，跳过写入。")
        return

    # 保存标题和描述
    content = f"""
请根据以下标题生成适合搜索和吸引点击的整个标题和说明描述，使用中文繁体字，主标题和副标题和相关标签写一起组合成整个标题,用|分开, 在整个标题和说明描述中包含用 | 分割的相关标签。整个标题需要便于搜索，足够接地气，容易出现在搜索列表中，并且富有吸引力，让人感兴趣，使人立即点击观看。说明描述的第一个段落一定是：

歡迎訂閱《爽剧风暴》的頻道哦 https://www.youtube.com/@SJFengBao?sub_confirmation=1
正版授權短劇，感謝大家支持！

主标题：
《{convert_simplified_to_traditional(sub_directory)}》【高清合集】【清晰音质】
    """

    # 写入文件
    with open(video_dest_result, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"文件 {video_dest_result} 已生成。")


# ffmpeg -i "release_video/aa测试目录/aa测试目录.mp4" -vf "drawtext=fontfile='ziti/fengmian/gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "release_video/aa测试目录/temp_output.mp4"
# ffmpeg -i "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录.mp4" -vf "drawtext=fontfile='C:\yuliu\workspace\yt-dlp\yuliu\ziti\fengmian\gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\temp_output.mp4"
# ffmpeg -i "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录.mp4" -vf "drawtext=fontfile='C:\yuliu\workspace\yt-dlp\yuliu\ziti\fengmian\gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,10)'" -c:a copy -y "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\temp_output.mp4"

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


def delete_files_by_list(frame_image_list):
    for file in frame_image_list:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except OSError:
            print(f"Failed to delete: {file}")


def delete_files(*args):
    # 合并所有传入的参数到一个列表
    all_files = []
    for arg in args:
        if isinstance(arg, str):
            all_files.append(arg)
        elif isinstance(arg, list):
            all_files.extend(arg)
        else:
            print(f"Unsupported input type: {type(arg)}")
            return

    # 尝试删除每个文件
    for file in all_files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except OSError as e:
            print(f"Failed to delete {file}: {e}")


# def check_directory(base_dir):
#     output_dir = os.path.join(base_dir, 'output')
#     output_pattern = re.compile(r"out_times_\d+_audio_vocals\.wav")
#
#     # 获取 input 和 output 目录下的所有子目录
#     sub_directories = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
#
#     for sub_dir in sub_directories:
#         input_files = [f for f in os.listdir(os.path.join(input_dir, sub_dir)) if input_pattern.match(f)]
#         output_files = [f for f in os.listdir(os.path.join(output_dir, sub_dir)) if output_pattern.match(f)]
#
#         if len(input_files) > 0 and len(input_files) == len(output_files):
#             return base_dir
#
#     return None


def extract_audio_only(video_path):
    # 生成新的文件路径
    base, ext = os.path.splitext(video_path)
    audio_only_path = f"{base}_audio.wav"  # 使用 .wav 扩展名

    # 如果文件已存在，直接返回
    if os.path.exists(audio_only_path):
        print(f"音频文件已存在: {audio_only_path}")
        return audio_only_path

    # 构建单个提取音频流的ffmpeg命令，使用-y选项覆盖现有文件
    command = [
        'ffmpeg', '-loglevel', 'quiet', '-i', video_path,
        '-map', '0:a', '-c:a', 'pcm_s16le', '-y', audio_only_path  # 确保使用 WAV 编码器
    ]

    # 打印命令以便手动检查
    print("运行命令: \n", " ".join(command))

    try:
        # 执行命令
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        result.check_returncode()  # 检查命令是否成功
        print(f"音频流提取成功: {audio_only_path}")

    except subprocess.CalledProcessError as e:
        print(f"发生错误: {e.stderr}")
        if os.path.exists(audio_only_path):
            os.remove(audio_only_path)  # 移除临时文件
        return None

    return audio_only_path


def get_user_confirmation():
    confirmation = input("请核对翻译文案对不对,会对完毕按 'y' 并且 Enter 继续: ")
    if confirmation.lower() == 'y':
        return True
    else:
        return False


def rename_file(original_video, sub_directory):
    # 获取文件目录和后缀
    directory, filename = os.path.split(original_video)
    _, extension = os.path.splitext(filename)
    # 新的文件路径
    new_path = os.path.join(directory, sub_directory + extension)
    # 如果目标文件已存在，删除它
    if os.path.exists(new_path):
        os.remove(new_path)
    # 重命名文件
    os.rename(original_video, new_path)
    # 返回新的文件路径
    return new_path


def get_mvsep_base_dir(is_high_quality, sub_directory):
    base_dir1 = os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2")
    base_dir2 = os.path.join(os.getcwd(), "MVSEP-CDX23-Cinematic-Sound-Demixing")
    base_dir1_out = os.path.join(base_dir1, "output", sub_directory)
    base_dir2_out = os.path.join(base_dir2, "output", sub_directory)

    # 判断 base_dir1_out 下面是否有文件
    if os.path.exists(base_dir1_out) and os.listdir(base_dir1_out):
        return base_dir1
    elif os.path.exists(base_dir2_out) and os.listdir(base_dir2_out):
        return base_dir2
    else:
        return base_dir1 if is_high_quality else base_dir2


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
             is_get_cover=False,

             is_get_fanyi=False,
             is_high_quality=False,
             cover_title_split_postion=0
             ):
    global download_cache_dir, release_video_dir, release_video_dir, mvsep_base_dir, mvsep_input_dir, mvsep_output_dir

    print_separator(f"初始化路径 <<{sub_directory}>>")

    download_cache_dir = get_dir("download_cache", sub_directory)
    release_video_dir = get_dir("release_video", sub_directory)

    # 定义两个目录
    mvsep_base_dir = get_mvsep_base_dir(is_high_quality, sub_directory)
    print(f"选择的目录是: {mvsep_base_dir}")

    mvsep_input_dir = get_dir(os.path.join(mvsep_base_dir, "input"), sub_directory)
    mvsep_output_dir = get_dir(os.path.join(mvsep_base_dir, "output"), sub_directory)
    ensure_directory_exists(download_cache_dir)
    ensure_directory_exists(release_video_dir)
    ensure_directory_exists(mvsep_input_dir)
    ensure_directory_exists(mvsep_output_dir)

    video_final = os.path.join(release_video_dir, f"{sub_directory}_zimu.mp4")
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
            print_separator(f"合并视频 {sub_directory}")
            original_video = os.path.join(release_video_dir, generate_md5_filename(videos))
            if not os.path.exists(original_video):
                original_video = merge_videos(videos, original_video)
        else:
            print_separator(f"复制视频文件到下载目录 <<{sub_directory}>>")
            target_path = os.path.join(release_video_dir, os.path.basename(videos[0]))
            shutil.copy(videos[0], target_path)
            original_video = target_path
    # 对原始视频重命名
    original_video = rename_file(original_video, sub_directory)
    frame_image_list = []
    if is_get_cover:
        # 记录开始时间
        print_separator(f"生成封面图 <<{sub_directory}>>")
        start_time = time.time()
        title_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 标题
        subtitle_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 副标题
        frame_image_list = extract_thumbnail_main(original_video,
                                                  release_video_dir,
                                                  cover_title,
                                                  title_font,
                                                  subtitle_font,
                                                  num_of_covers=num_of_covers,
                                                  crop_height=100,
                                                  isTest=False,
                                                  cover_title_split_postion=cover_title_split_postion
                                                  )

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"获取{num_of_covers}张图片时间: {elapsed_time:.2f} 秒, 平均每张: {elapsed_time / num_of_covers:.2f} 秒")

        generate_video_metadata(release_video_dir, sub_directory)

    if is_get_video:
        if os.path.exists(video_final) and has_zimu_suffix(video_final):
            print(f"文件 : 存在,有字幕,有水印: {video_final}")
            # print(f"{get_file_name_with_extension(dest_video_path)}已存在，不需要再处理了,直接返回")
            # target_languages = ["es", "hi", "ar", "pt", "fr", "de", "ru", "ja"]
            # audio_paths = get_sorted_vocals_wav_files(release_video_dir)
            # output_zh_srt_path = transcribe_audio_to_srts(audio_paths)
            # subtitle_paths, video_path = process_videos(dest_video_path, ["en"])
            # print_separator()
        else:
            print_separator(f"1.处理视频,切成小块视频,进行处理 <<{sub_directory}>>")
            video_nobgm = os.path.join(release_video_dir, f"{sub_directory}_nobgm{get_file_only_extension(original_video)}")
            print(f"\n原始视频路径: {original_video}")
            video_duration = get_mp4_duration(original_video)
            print(f"\n原始视频时长: {video_duration}")
            keyframeextractor = KeyFrameExtractor(original_video, cache_util)
            keyframe_times = keyframeextractor.extract_keyframes()
            split_points = find_split_points(keyframe_times, split_time_ms)
            video_clips = segment_video_times(original_video, split_points)
            print(f"\n原始视频已拆分成{len(video_clips)}份,将逐一进行音频处理")

            print_separator(f"2.对视频人声分离 <<{sub_directory}>>")

            (video_dest_list, audio_origin_list,
             video_origin_list, audio_vocals_list,
             video_origin_clips, process_video_time) = process_video_files_list(video_clips)

            video_nobgm = merge_videos(video_dest_list, video_nobgm)

            audio_path_wav = extract_audio_only(video_nobgm)
            print_separator(f"添加英文字幕,如果字幕不存在,就生成,还附带其他语言字幕,主要用到的是英文字幕 <<{sub_directory}>>")
            # 音频 转录 生成 中文字幕
            zh_srt = transcribe_audio_to_srt(audio_path=audio_path_wav, language='cmn', sub_directory=sub_directory)

            # 用 中文字幕 翻译 生成 英文字幕
            en_srt = yuliu.transcribe_srt.translate_srt_file(zh_srt, 'en', max_payload_size=2048)
            ##以上步骤保证一定有英文字幕了
            print(f"====================添加英文字幕和水印<<{sub_directory}>>======================")
            # 添加英文字幕和水印
            video_nobgm, video_final = add_zimu_shuiyin_to_video(video_nobgm, en_srt)
            process_and_save_results(original_video, download_time, process_video_time, result_file_name, sub_directory)
            # 生成视频metadata
            delete_files(audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips)

    if is_get_fanyi:
        try:
            print_separator(f"3.生成翻译字幕文件，供上传youtube平台，与视频无关 ({cover_title})")
            zh_srt = os.path.join(release_video_dir, f"{sub_directory}_cmn.srt")
            video_nobgm = os.path.join(release_video_dir, f"{sub_directory}_nobgm.mp4")

            en_srt = yuliu.transcribe_srt.translate_srt_file(zh_srt, 'en', max_payload_size=2048)

            ##以上步骤保证一定有英文字幕了
            print(f"====================添加英文字幕和水印<<{sub_directory}>>======================")
            # 添加英文字幕和水印
            video_nobgm, video_final = add_zimu_shuiyin_to_video(video_nobgm, en_srt)

            print(f"====================生成 8 国翻译<<{sub_directory}>>======================")
            target_languages = ["spa", "hin", "arb", "por", "fra", "deu", "rus", "jpn"]
            for code in target_languages:
                yuliu.transcribe_srt.translate_srt_file(zh_srt, code, max_payload_size=2048)

            # zh_srt = os.path.join(release_video_dir, f'{sub_directory}_zh.srt')
            # result_other_srt = process_videos([zh_srt], target_languages)
            # for language in target_languages:
            #     concatenated_subs = concatenate_srt_files(result_other_srt[language])
            #     zh_srt = os.path.join(release_video_dir, f'{sub_directory}_{language}.srt')
            #     concatenated_subs.save(zh_srt, encoding='utf-8')
            # print_separator()
            # return
        except Exception as e:
            print(f'出错: {e}')

    cache_util.close_cache()
