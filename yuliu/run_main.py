import glob
import os
import re
import shutil
import subprocess
import time

from torchvision.datasets.utils import calculate_md5

from utils import get_mp4_duration, \
    find_split_points, \
    print_separator, segment_video_times, merge_videos, minutes_to_milliseconds, separate_audio_and_video_list, merge_audio_and_video_list, CommandExecutor, \
    print_red, print_yellow, get_path_without_suffix
from yuliu import voice_utils, transcribe_srt
from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.check_utils import is_banned
from yuliu.check_final import correct_subtitles
from yuliu.extract_thumbnail_main import extract_thumbnail_main
from yuliu.keyframe_extractor import KeyFrameExtractor
from yuliu.transcribe_video import transcribe_audio_to_srt
from yuliu.zimu_utils import add_final_shuiyin_to_video

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def delete_directory_contents(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print_red(f'删除 {file_path} 时出错: {e}')
        print(f'已清空目录: {directory}')
    else:
        print(f'目录不存在: {directory}')


# 清除缓存逻辑
def clear_cache():
    directories_to_clear = [
        # download_cache_dir,
        # release_video_dir,
        mvsep_input_dir,
        mvsep_output_dir
    ]
    print("clear_cache")
    for directory in directories_to_clear:
        delete_directory_contents(directory)


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
    delete_directory_contents(mvsep_input_dir)
    for audio_file in audio_files:
        shutil.copy(audio_file, mvsep_input_dir)

    if not all(os.path.exists(file) for file in output_file_vocals_list):
        print(f"并不所有文件都存在。清空目录{mvsep_output_dir}")
        # clear_directory_contents(mvsep_output_dir)
        try:
            mvsep_main = os.path.join(mvsep_base_dir, 'mvsep_main.py')
            command = ['python', f'{mvsep_main}', '--input', mvsep_input_dir, '--output', mvsep_output_dir]
            print(' '.join(command))
            CommandExecutor.run_command(command)
            # subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        except Exception as e:
            print_red(f"处理音频文件时发生错误: {e}")
    else:
        print("所有文件都存在。")
    elapsed_time = time.time() - start_time
    print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")

    out_times_dir = os.path.join(src_path, "out_times")
    os.makedirs(out_times_dir, exist_ok=True)
    # # 清楚以前的,添加到images 目录中去
    for output_file_vocals in output_file_vocals_list:
        if os.path.exists(output_file_vocals):
            destination = shutil.copy(output_file_vocals, out_times_dir)
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
    audio_origin_list = []
    video_origin_list = []
    audio_vocals_list = []

    for index, video_file_item in enumerate(video_origin_clips, start=1):
        pre_name = os.path.splitext(video_file_item)[0]
        video_dest_list.append(pre_name + '_processed.mp4')
        audio_origin_list.append(pre_name + '_audio.mp3')
        video_origin_list.append(pre_name + '_video.mp4')
        audio_vocals_list.append(pre_name + '_audio_vocals.wav')

    if all(os.path.isfile(file) for file in video_dest_list):
        process_video_time = time.time() - start_time
        return video_dest_list, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, process_video_time
    else:
        # 多线程分割视频
        audio_origin_list, video_origin_list = separate_audio_and_video_list(video_origin_clips)
        # 单线程去除视频背景音乐
        audio_vocals_list = process_audio_with_mvsep_mdx23_list(audio_origin_list)

        video_dest_list = merge_audio_and_video_list(video_origin_list, audio_vocals_list, video_dest_list)

        process_video_time = time.time() - start_time
        return video_dest_list, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, process_video_time


def add_timestamp_to_filename(file_path):
    # 提取当前时间戳
    timestamp = int(time.time())
    # 获取文件路径和扩展名
    base_path, file_extension = os.path.splitext(file_path)
    # 创建新的文件路径，带有时间戳
    new_file_path = f"{base_path}_{timestamp}{file_extension}"
    # 重命名文件
    os.rename(file_path, new_file_path)


def my_hook(d):
    if d['status'] == 'finished':
        print(f"下载完成: {d['filename']}")


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"删除文件: {file_path}")
    except OSError as e:
        print(f"删除文件时出错: {e}")


import os


def generate_video_metadata(release_video_dir, sub_directory):
    # 创建目录（如果不存在）
    os.makedirs(release_video_dir, exist_ok=True)

    # 文件路径
    video_dest_result = f"{release_video_dir}/{sub_directory}.txt"

    # 保存标题和描述
    content = f"""
请根据以下标题生成适合搜索和吸引点击的整个标题和说明描述，
要求如下:
1.我需10种不同国家语言的版本(一个都不能少),分别是英文,中文台湾繁体,西班牙语,印地语,阿拉伯语,葡萄牙语,法语,德语,日语,韩语
2.整个标题组成:主标题和副标题和标签从左到右顺序一整行,标签最后用' | '隔开,整个标题总长度不超过90个字符。
3.说明描述中也包含用|分割的相关标签,别超过500字符
4.整个标题要便于搜索，足够接地气，容易出现在搜索列表中，
5.整个标题富有吸引力，让人感兴趣，使人立即点击观看。
6.你回答的格式都按照下面格式返回,如下:
整个标题:
xxx
说明描述:
xxx(第一个段落)
xxx
7.说明描述的第一个段落一定是(需要根据语言进行翻译)：
欢迎订阅《爽剧风暴》的频道哦 https://www.youtube.com/@SJFengBao?sub_confirmation=1
正版授权短剧，感谢大家支持！

我的标题是：
《{sub_directory}》【高清合集】
    """

    # 写入文件（覆盖已存在的文件）
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


def delete_files_by_list(*args):
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
    clear_cache()
    # 尝试删除每个文件
    for file in all_files:
        delete_file(file)


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




# 检查base是否包含下划线
def extract_audio_only_add60(video_path):
    # 定义输出文件路径
    base_dir = os.path.dirname(video_path)
    extracted_audio_path = os.path.join(base_dir, 'extracted_audio.wav')
    silence_path = os.path.join(base_dir, 'silence.wav')

    base, ext = os.path.splitext(video_path)
    base_name = get_path_without_suffix(base)
    audio_only_path = f"{base_name}.wav"  # 使用 .wav 扩展名

    # 如果文件已存在，直接返回
    if os.path.exists(audio_only_path):
        print_yellow(f"音频文件已存在: {audio_only_path}")
        return audio_only_path

    try:
        # Step 1: 提取音频
        subprocess.run([
            'ffmpeg', '-loglevel', 'quiet', '-i', video_path,
            '-map', '0:a', '-c:a', 'pcm_s16le', '-y', extracted_audio_path
        ], check=True)

        # Step 2: 生成 30 秒静音文件
        subprocess.run([
            'ffmpeg', '-loglevel', 'quiet', '-f', 'lavfi',
            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-t', '30', '-c:a', 'pcm_s16le', '-y', silence_path
        ], check=True)

        # Step 3: 连接静音和提取的音频
        subprocess.run([
            'ffmpeg', '-loglevel', 'quiet',
            '-i', silence_path, '-i', extracted_audio_path, '-i', silence_path,
            '-filter_complex', '[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]',
            '-map', '[a]', '-c:a', 'pcm_s16le', '-y', audio_only_path
        ], check=True)

        # 清理临时文件
        delete_file(extracted_audio_path)
        delete_file(silence_path)

        print(f'生成的音频文件已保存到: {audio_only_path}')
        return audio_only_path

    except subprocess.CalledProcessError as e:
        print(f"发生错误: {e.stderr}")
        delete_file(audio_only_path)
        return None


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
    delete_file(new_path)
    # 重命名文件
    os.rename(original_video, new_path)
    # 返回新的文件路径
    return new_path


def check_files(release_video_dir, num_of_covers):
    frame_pattern = os.path.join(release_video_dir, 'images', 'frame_*.jpg')
    input_img_pattern = os.path.join(release_video_dir, 'images', 'input_img*.png')

    frame_files = glob.glob(frame_pattern)
    input_img_files = glob.glob(input_img_pattern)

    return len(frame_files) == num_of_covers * 3 and len(input_img_files) == num_of_covers


def run_main(url=None,

             cover_title=None,
             split_time_min=15,

             is_only_download=False,
             sub_directory=None,
             is_test=False,

             video_download_name=None,
             is_get_video=True,
             num_of_covers=1,
             is_get_cover=False,

             is_get_fanyi=False,
             cover_title_split_postion=0
             ):
    global src_path, release_video_dir, release_video_dir, mvsep_base_dir, mvsep_input_dir, mvsep_output_dir

    print_separator(f"初始化路径 : {sub_directory}")

    if is_banned(sub_directory):
        print_red(f"{sub_directory} 这个视频被禁播了,不能上传")
        return
    else:
        print(f"{sub_directory} 这个视频能上传")

    release_video_dir = get_dir("release_video", sub_directory)

    # 定义两个目录
    mvsep_base_dir = os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2")
    print(f"选择的目录是: {mvsep_base_dir}")

    mvsep_input_dir = get_dir(os.path.join(mvsep_base_dir, "input"), sub_directory)
    mvsep_output_dir = get_dir(os.path.join(mvsep_base_dir, "output"), sub_directory)
    src_path = os.path.join(release_video_dir)

    ensure_directory_exists(release_video_dir)
    ensure_directory_exists(mvsep_input_dir)
    ensure_directory_exists(mvsep_output_dir)
    ensure_directory_exists(src_path)

    original_video = os.path.join(src_path, f"{sub_directory}.mp4")
    video_nobgm = os.path.join(src_path, f"{sub_directory}_nobgm.mp4")
    video_final = os.path.join(src_path, f"{sub_directory}_nobgm_final.mp4")

    cache_util = DiskCacheUtil()

    split_time_ms = minutes_to_milliseconds(split_time_min)
    if is_test:
        previous_split_time = cache_util.get_from_cache("test_split_time_ms", 0.5)
    else:
        previous_split_time = cache_util.get_from_cache("split_time_ms", 900 * 1000)

    print(f"上次切割时间单位:{previous_split_time}毫秒")
    print(f"当前切割时间单位:{split_time_ms}毫秒")
    if previous_split_time is None or previous_split_time != split_time_ms:
        print("更新切割时间")
        if is_test:
            clear_cache()
            cache_util.set_to_cache("test_split_time_ms", split_time_ms)
        else:
            clear_cache()
            cache_util.set_to_cache("split_time_ms", split_time_ms)
    if is_test:
        clear_cache()

    if is_get_cover:
        # 记录开始时间
        try:
            print_separator(f"获取封面图 : {sub_directory}")
            start_time = time.time()
            title_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 标题
            subtitle_font = os.path.join('ziti', 'hongleibanshu', 'hongleibanshu.ttf')  # 副标题

            crop_bottom = 150
            crop_left = 426 / 720 * crop_bottom
            crop_dict = {
                'crop_left': crop_left,
                'crop_right': 0,
                'crop_top': 0,
                'crop_bottom': crop_bottom
            }

            if not check_files(release_video_dir, num_of_covers):
                extract_thumbnail_main(video_nobgm if os.path.exists(video_nobgm) else original_video,
                                       cover_title,
                                       title_font,
                                       subtitle_font,
                                       crop_dict,
                                       num_of_covers=num_of_covers,
                                       isTest=False,
                                       cover_title_split_postion=cover_title_split_postion
                                       )
            print(f"获取封面情况:获取{num_of_covers}张图片时间: {(time.time() - start_time):.2f} 秒, "
                  f"平均每张: {(time.time() - start_time) / num_of_covers:.2f} 秒")
            print(f"\n总耗时情况:{(time.time() - start_time)}")

            # generate_video_metadata(release_video_dir, sub_directory)
        except Exception as e:
            print_red(f'出错: {e}')

    if is_get_video:
        try:
            print_separator(f"获取无背景音乐视频 : {sub_directory}")

            audio_origin_list = []
            video_origin_list = []
            audio_vocals_list = []
            video_origin_clips = []
            video_clips = []

            if not os.path.exists(video_final):
                start_time = time.time()

                print(f"1.处理视频,切成小块视频,进行处理 <<{sub_directory}>>")
                if not os.path.exists(video_nobgm):
                    print(f"\n原始视频路径: {original_video}")
                    video_duration = get_mp4_duration(original_video)
                    print(f"\n原始视频时长: {video_duration}")
                    keyframeextractor = KeyFrameExtractor(original_video, cache_util)
                    keyframe_times = keyframeextractor.extract_keyframes()
                    split_points = find_split_points(keyframe_times, split_time_ms)
                    video_clips = segment_video_times(original_video, split_points)

                    print(f"\n原始视频已拆分成{len(video_clips)}份,将逐一进行音频处理")

                    print(f"2.对视频人声分离 <<{sub_directory}>>")
                    (video_dest_list, audio_origin_list,
                     video_origin_list, audio_vocals_list,
                     video_origin_clips, process_video_time) = process_video_files_list(video_clips)
                    video_nobgm = merge_videos(video_dest_list, video_nobgm)

                zh_srt = transcribe_audio_to_srt(video_nobgm, language='zh', sub_directory=sub_directory)
                # 修正翻译
                zh_srt = correct_subtitles(video_nobgm, False)
                # if not is_test:

                # base, ext = os.path.splitext(video_nobgm)
                # audio_only_path = f"{base}_audio.wav"  # 使用 .wav 扩展名

                base, ext = os.path.splitext(video_nobgm)
                audio_only_path = f"{base}_audio.wav"  # 使用 .wav 扩展名
                out_times = os.path.join(release_video_dir, 'out_times')
                if os.path.exists(video_nobgm):
                    os.remove(original_video)

                delete_directory_contents(out_times)
                delete_files_by_list(audio_only_path, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, video_clips)

                print(f"\n总耗时情况:{(time.time() - start_time)}")

            else:

                base, ext = os.path.splitext(video_nobgm)
                audio_only_path = f"{base}_audio.wav"  # 使用 .wav 扩展名
                out_times = os.path.join(release_video_dir, 'out_times')
                if os.path.exists(video_nobgm):
                    delete_file(original_video)

                delete_directory_contents(out_times)

                delete_files_by_list(audio_only_path, audio_origin_list, video_origin_list, audio_vocals_list, video_origin_clips, video_clips)

                print_yellow(f"{os.path.relpath(video_final, './')} 最终视频 已经存在")
        except Exception as e:
            print_red(f'出错: {e}')

    if is_get_fanyi:
        try:
            print_separator(f"翻译,字幕,水印 : <<{sub_directory}>>")
            start_time = time.time()
            zh_srt = transcribe_audio_to_srt(video_nobgm, language='zh', sub_directory=sub_directory)
            # 修正翻译
            zh_srt = correct_subtitles(video_nobgm, False)

            en_srt = transcribe_srt.translate_srt_file(zh_srt, 'en', 256 * 6)
            zh_tw_srt = transcribe_srt.translate_srt_file(zh_srt, 'zh-TW', 256 * 8 / 4)
            video_nobgm, video_final = add_final_shuiyin_to_video(video_nobgm, en_srt)

            print(f"\n4.翻译 8 国翻译 srt文件 <<{sub_directory}>>")

            # target_languages = ["es", "hi", "ar", "pt", "fr", "de", "ja", "ko"]
            # for code in target_languages:
            #     transcribe_srt.translate_srt_file(corrected_zh_srt, code, max_payload_size=102400)

            generate_video_metadata(release_video_dir, sub_directory)
            print(f"\n总耗时情况:{(time.time() - start_time)}")
            voice_utils.play_voice_message(f'成功合成 {sub_directory} 可发布视频')
        except Exception as e:
            print_red(f'出错: {e}')

    cache_util.close_cache()
