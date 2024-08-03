import concurrent.futures
import hashlib
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import psutil

from yuliu.DiskCacheUtil import DiskCacheUtil


class CommandExecutor:
    @staticmethod
    def read_output(pipe, log_file, pattern=None):
        try:
            for line in iter(pipe.readline, ''):
                if pattern is None or re.search(pattern, line):
                    print(line.strip())
                    log_file.write(line)
        finally:
            pipe.close()

    @staticmethod
    def run_command(command, pattern=None):
        start_time = time.time()
        try:
            process = subprocess.Popen(
                command,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True,
                errors='ignore'
            )

            with open("ffmpeg_output.log", "w", encoding="utf-8", errors='ignore') as log_file:
                stdout_thread = threading.Thread(target=CommandExecutor.read_output, args=(process.stdout, log_file, pattern))
                stderr_thread = threading.Thread(target=CommandExecutor.read_output, args=(process.stderr, log_file, pattern))

                stdout_thread.start()
                stderr_thread.start()

                process.wait()

                stdout_thread.join()
                stderr_thread.join()

        except subprocess.CalledProcessError as e:
            print("执行命令时发生错误.")
            if e.stderr:
                print(f"错误输出:\n{e.stderr}")
            print(f"返回代码: {e.returncode}")
        except Exception as e:
            print_red(f"执行命令时发生未知错误: {e}")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()

        end_time = time.time()
        elapsed_time = end_time - start_time
        if isinstance(command, list):
            command_str = ' '.join(command)
        else:
            command_str = command
        print(f"\n命令执行成功\n: {command_str}\n")
        print(f"命令执行耗时: {elapsed_time:.2f} 秒")


def print_red(text):
    print(f"\033[91m{text}\033[0m")


def print_yellow(text):
    print(f"\033[93m{text}\033[0m")


def print_separator(text='', char='=', length=150):
    """
    打印一个带有文本的分隔符线。
    参数:
    text (str): 要显示的文本，默认为空。
    char (str): 用于创建分隔符线的字符，默认为 '='。
    length (int): 分隔符线的总长度，默认为 100。
    """
    if text:
        half_length = (length - len(text) - 2) // 2
        separator = f"{char * half_length} {text} {char * half_length}"
        if len(separator) < length:
            separator += char * (length - len(separator))
    else:
        separator = char * length
    print_yellow(f'\n\n{separator}\n')


def get_file_creation_time(file_path):
    return os.path.getctime(file_path)


def get_file_only_name(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_only_extension(file_path):
    import os
    return os.path.splitext(file_path)[1]


def get_file_name_with_extension(file_path):
    import os
    return os.path.basename(file_path)


def merge_single_audio_video(video_file, audio_file, result_file):
    # 如果文件已存在，直接返回
    if os.path.exists(result_file):
        print(f"{get_file_only_name(result_file)} 已经存在，直接返回。")
        return result_file

    print(f"合并音频: {get_file_only_name(audio_file)} 和视频: {get_file_only_name(video_file)} 到: {get_file_only_name(result_file)}")
    command = [
        'ffmpeg',
        '-loglevel', 'quiet',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',  # 视频流不重新编码，直接复制
        '-c:a', 'aac',  # 将音频流编码为AAC格式
        '-b:a', '192k',  # 设置音频比特率
        '-strict', 'experimental',  # 使用实验性AAC编码器
        '-y',  # 覆盖输出文件
        result_file
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    return result_file


def merge_audio_and_video_list(video_files, audio_files, result_files):
    if len(video_files) != len(audio_files) or len(audio_files) != len(result_files):
        raise ValueError("视频、音频和结果文件的列表长度必须一致")
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(merge_single_audio_video, v, a, r) for v, a, r in zip(video_files, audio_files, result_files)]
        result_files = [future.result() for future in futures]
    elapsed_time = time.time() - start_time
    print(f"耗时: {elapsed_time:.2f} 秒\n")
    return result_files


def get_mp4_duration(file_path):
    # file_path=os.path.abspath(file_path)
    print(f"\n获取 MP4 文件时长: {file_path}")
    try:
        command = [
            'ffprobe',
            '-loglevel', 'quiet',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'format=duration',
            '-of', 'json',
            file_path
        ]
        print(' '.join(command))
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            duration_json = json.loads(result.stdout)
            duration_seconds = float(duration_json['format']['duration'])
            duration_milliseconds = int(duration_seconds * 1000)
            print(f"{os.path.basename(file_path)} 视频时长: {duration_milliseconds} 毫秒")
            return duration_milliseconds
    except subprocess.CalledProcessError as e:
        print(f"ffprobe 错误: {e.stderr}")
        raise RuntimeError(f"ffprobe 错误: {e.stderr}")


def extract_audio_and_video(video_path):
    print(f"从视频中分离音频和视频: {video_path}")
    start_time = time.time()
    base, _ = os.path.splitext(video_path)
    audio_output, video_output = f"{base}_audio.mp3", f"{base}_video.mp4"
    if not os.path.exists(audio_output) or not os.path.exists(video_output):
        command = [
            'ffmpeg', '-i', video_path,
            '-map', '0:a', '-acodec', 'libmp3lame', audio_output,
            '-map', '0:v', '-vcodec', 'copy', video_output,
            '-y', '-loglevel', 'quiet'
        ]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        # 联合提取音频和视频，不重新编码
        # (ffmpeg.input(video_path)
        #  .output(audio_output, map='0:a', codec='copy')
        #  .output(video_output, map='0:v', codec='copy', an=None)
        #  .run(quiet=True, overwrite_output=True))
        # print(f"音频提取到: {audio_output}")
        # print(f"视频提取到: {video_output}")

    elapsed_time = time.time() - start_time
    print(f"耗时: {elapsed_time:.2f} 秒")

    return audio_output, video_output


def separate_audio_and_video_list(video_paths):
    audio_outputs = [None] * len(video_paths)
    video_outputs = [None] * len(video_paths)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(extract_audio_and_video, video_path): index for index, video_path in enumerate(video_paths)}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            audio_output, video_output = future.result()
            audio_outputs[index] = audio_output
            video_outputs[index] = video_output
    return audio_outputs, video_outputs


# 调用示例
# video_files = ["path/to/your/video1.mp4", "path/to/your/video2.mp4"]
# separate_audio_and_video(video_files)


import os


def separate_audio_and_video(video_path):
    print(f"\n从视频中分离音频和视频: {video_path}")
    start_time = time.time()
    base, _ = os.path.splitext(video_path)
    audio_output, video_output = f"{base}_audio.mp3", f"{base}_video.mp4"

    if not os.path.exists(audio_output) or not os.path.exists(video_output):
        command = [
            'ffmpeg', '-i', video_path,
            '-map', '0:a', '-acodec', 'libmp3lame', audio_output,
            '-map', '0:v', '-vcodec', 'copy', video_output
        ]
        command += ['-loglevel', 'quiet']
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"音频提取到: {audio_output}")
        print(f"视频提取到: {video_output}")

    elapsed_time = time.time() - start_time
    print(f"耗时: {elapsed_time:.2f} 秒")
    return audio_output, video_output


# 缓存文件路径
CACHE_FILE_PATH = 'keyframe_cache.json'


# 加载缓存文件
def load_cache():
    import os
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as f:
            return json.load(f)
    return {}


# 保存缓存文件
def save_cache(cache):
    with open(CACHE_FILE_PATH, 'w') as f:
        json.dump(cache, f, indent=4)


# 初始化缓存
keyframe_cache = load_cache()


def calculate_md5(file_path):
    """计算文件的MD5值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    md5_result = hash_md5.hexdigest()
    return md5_result


def generate_unique_key(file_path):
    """生成唯一key值"""
    if not os.path.isfile(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    file_md5 = calculate_md5(file_path)
    unique_key = f"{file_path}_{file_md5}"
    return unique_key


def find_split_points(keyframe_times, split_time_ms):
    split_time = split_time_ms / 1000.0  # 将毫秒转换为秒
    split_points = []
    current_time = 0.0

    # 将 keyframe_times 列表中的每个 pkt_pts_time 时间戳转换为浮点数
    keyframe_times = [float(frame['pkt_pts_time']) for frame in keyframe_times]

    for keyframe_time in keyframe_times:
        if keyframe_time - current_time >= split_time and keyframe_time not in (0.0, keyframe_times[-1]):
            split_points.append(keyframe_time)
            current_time = keyframe_time

    print(f"\n拆分列表split_points:\n{split_points}\n")
    return split_points


def concatenate_videos(video_list, merged_output):
    print(f"\n拼接视频文件列表: {video_list}")
    print(f"\n拼接完成的视频 merged_output: {merged_output}")

    # 检查输出文件是否已存在
    if os.path.exists(merged_output):
        print(f"{merged_output} 已经存在，跳过拼接。")
        return merged_output

    video_dir = os.path.dirname(video_list[0])
    if len(video_list) > 1:
        for video in video_list:
            if not os.path.exists(video):
                raise FileNotFoundError(f"文件不存在: {video}")

        input_txt_path = os.path.join(video_dir, 'input.txt')
        with open(input_txt_path, 'w', encoding='utf-8') as file:
            for video in video_list:
                abs_video_path = os.path.abspath(video)
                file.write(f"file '{abs_video_path}'\n")

        with open(input_txt_path, 'r', encoding='utf-8') as file:
            print(file.read())

        try:
            command = [
                'ffmpeg',
                '-loglevel', 'quiet',
                '-f', 'concat',
                '-safe', '0',
                '-i', input_txt_path,
                '-c', 'copy',
                merged_output
            ]
            command += ['-loglevel', 'quiet']
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        except subprocess.CalledProcessError as e:
            print(f"拼接过程中出错: {e}")
        finally:
            if os.path.exists(input_txt_path):
                os.remove(input_txt_path)
                # for video in video_list:
                #     if os.path.exists(video):
                #         os.remove(video)

        return merged_output
    else:
        shutil.move(video_list[0], merged_output)
        return merged_output


def close_chrome():
    for proc in psutil.process_iter(['name']):
        if 'chrome' in proc.info['name'].lower() or 'chromium' in proc.info['name'].lower():
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.NoSuchProcess:
                continue
            except psutil.TimeoutExpired:
                proc.kill()


def generate_md5_filename(video_list, prefix="video", extension=".mp4", length=8):
    # 将视频文件名按顺序连接起来
    concatenated_names = "".join(video_list)
    # 计算 MD5 哈希值
    md5_hash = hashlib.md5(concatenated_names.encode()).hexdigest()
    # 截取 MD5 哈希值的前 length 位
    short_md5_hash = md5_hash[:length]
    # 生成唯一文件名
    unique_filename = f"{prefix}_{short_md5_hash}{extension}"
    return unique_filename


def format_duration(duration_milliseconds):
    hours = duration_milliseconds // 3600000
    minutes = (duration_milliseconds % 3600000) // 60000
    seconds = (duration_milliseconds % 60000) // 1000
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def format_seconds(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def save_unknown_duration_result(file_name, download_time, process_time, result_file_name):
    with open(result_file_name, "a", encoding='utf-8') as file:
        file.write(f"{file_name} : 未知时长 : 下载-{download_time:.2f}秒 : {process_time:.2f}秒\n")


def process_and_save_results(original_video, download_time, process_video_time, result_file_name, video_name):
    video_duration = get_mp4_duration(original_video)

    if video_duration:
        duration_seconds = video_duration / 1000.0
        video_duration_minutes = duration_seconds / 60.0
        ratio_value = process_video_time / video_duration_minutes
    else:
        duration_seconds = None
        video_duration_minutes = None
        ratio_value = None

    # file_name = os.path.basename(original_video).replace('.mp4', '')
    if video_duration_minutes is not None and ratio_value is not None:
        if ratio_value > 10:
            save_result(video_name, duration_seconds, download_time, process_video_time, ratio_value, result_file_name)
    else:
        save_unknown_duration_result(video_name, download_time, process_video_time, result_file_name)

    print(f"结果保存到文件: {result_file_name}")


def save_result(file_name, duration_seconds, download_time, process_time, ratio_value, result_file_name):
    duration_str = format_seconds(duration_seconds)
    download_str = format_seconds(download_time)
    process_str = format_seconds(process_time)
    with open(result_file_name, "a", encoding='utf-8') as file:
        file.write(
            f"{file_name} : 视频时长_{duration_seconds:.2f}秒({duration_str}) : 下载_{download_time:.2f}秒({download_str}) : 除音乐_{process_time:.2f}秒({process_str}) : {ratio_value:.2f}/min\n")


def resize_images_if_needed(images, max_width=1920, max_height=1080):
    def is_resolution_gte_1920x1080(img_path):
        with Image.open(img_path) as img:
            width, height = img.size
            return width >= 1920 and height >= 1080

    for image in images:
        if is_resolution_gte_1920x1080(image):
            try:
                with Image.open(image) as img:
                    width, height = img.size
                    if width > max_width or height > max_height:
                        ratio = min(max_width / width, max_height / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        img_resized.save(image)
            except Exception as e:
                print_red(f"无法处理图像 {image}。错误信息：{e}")


from PIL import Image


def convert_jpeg_to_png(input_imgs):
    """
    将一组 JPEG 图像转换为 PNG 格式，并打印图像的原始和转换后的格式及尺寸。
    转换成功后删除原始 JPEG 图像。

    参数：
    - input_imgs: list, 图像文件路径的列表。

    返回值：
    - list, 新图片的路径列表
    """
    new_image_paths = []

    for input_img in input_imgs:
        try:
            with Image.open(input_img) as img:
                if img.format == 'JPEG':
                    base_name = os.path.basename(input_img)
                    dir_name = os.path.dirname(input_img)
                    new_file_name = os.path.join(dir_name, os.path.splitext(base_name)[0] + '.png')
                    img.save(new_file_name, 'PNG')
                    with Image.open(new_file_name) as new_img:
                        width, height = new_img.size
                    os.remove(input_img)
                    new_image_paths.append(new_file_name)
        except Exception as e:
            print_red(f"错误: {e}")
            pass

    return new_image_paths


def get_ffmpeg_version():
    command = ['ffmpeg', '-version']
    try:
        process = subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        stdout, stderr = process.communicate()
        if process.returncode == 0:
            for line in stdout.split('\n'):
                if 'ffmpeg version' in line:
                    version_info = line.split()
                    if len(version_info) > 2:
                        version = version_info[2]
                        return version
        else:
            print(f"Error checking FFmpeg version:\n{stderr}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"执行命令时发生错误: {e}")
        if e.stderr:
            print(f"错误输出:\n{e.stderr}")
        print(f"返回代码: {e.returncode}")
        return None


# 调用示例


def files_exist(file_list):
    return all(os.path.exists(file) for file in file_list)


def segment_video_times(original_video, split_points):
    start_time = time.time()
    print("开始分割视频")

    out_times_dir = os.path.join(os.path.dirname(original_video), 'out_times')
    os.makedirs(out_times_dir, exist_ok=True)
    output_pattern = os.path.join(out_times_dir, 'out_times_%02d.mp4')
    cache_util = DiskCacheUtil()
    # 计算命令的MD5哈希值
    times_str = ",".join(map(str, split_points))
    command = f'ffmpeg -i "{original_video}" -f segment -segment_times {times_str} -c copy -map 0 "{output_pattern}" -loglevel quiet'
    command_hash = hashlib.md5(command.encode('utf-8')).hexdigest()

    file_list = cache_util.get_from_cache(command_hash)

    if file_list and files_exist(file_list):
        print("使用缓存结果")
    else:
        if not split_points:
            print("无有效的分割时间点，返回原始文件。")
            output_file = output_pattern.replace('%02d', '00')
            shutil.copyfile(original_video, output_file)
            file_list = [output_file]
        else:
            print(f"执行命令: {command}")
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            # 生成输出文件列表
            num_segments = len(split_points) + 1
            file_list = [output_pattern.replace('%02d', f'{i:02d}') for i in range(num_segments)]
            # 保存结果到缓存
            cache_util.set_to_cache(command_hash, file_list)

    end_time = time.time()
    print(f"生成的文件列表: {file_list}")
    print(f"分割耗时: {end_time - start_time:.2f}秒")

    cache_util.close_cache()

    return file_list


def minutes_to_milliseconds(minutes):
    return minutes * 60 * 1000


import shutil


def merge_videos(file_list, output_file):
    if os.path.exists(output_file):
        print(f"{output_file} 已存在，直接返回")
        return output_file

    if len(file_list) == 1:
        print(f"只有一个文件，无需合并，复制 {file_list[0]} 为 {output_file}")
        shutil.copy(file_list[0], output_file)
        return output_file
    try:
        with open('filelist.txt', 'w', encoding='utf-8') as f:
            for file in file_list:
                f.write(f"file '{file}'\n")
        with open('filelist.txt', 'r', encoding='utf-8') as f:
            print(f"filelist.txt 内容:\n{f.read()}")
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'filelist.txt', '-c', 'copy', output_file,
            '-loglevel', 'quiet'
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    finally:
        os.remove('filelist.txt')
    return output_file


def extract_first_5_minutes(original_video, release_video_dir):
    """截取前5分钟的视频并移动到指定目录"""
    base_name, ext = os.path.splitext(os.path.basename(original_video))
    output_video = f"{base_name}_5min{ext}"
    output_path = os.path.join(release_video_dir, output_video)
    # 确保输出目录存在
    os.makedirs(release_video_dir, exist_ok=True)

    # 如果文件已经存在，不再重新生成
    if os.path.exists(output_path):
        print(f"\n文件已存在: {output_path},不需要重新生成测试视频\n")
        return output_path

    command = [
        'ffmpeg',
        '-i', original_video,
        '-t', '00:05:00',
        '-c', 'copy',
        '-y',  # 添加覆盖参数
        output_path
    ]
    command += ['-loglevel', 'quiet']
    subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')

    if os.path.exists(output_path):
        print(f"成功生成视频: {output_path}")
        return output_path
    else:
        raise FileNotFoundError(f"未能生成视频: {output_path}")


from opencc import OpenCC


def convert_simplified_to_traditional(text):
    try:
        cc = OpenCC('s2t')
        return cc.convert(text)
    except Exception as e:
        print_red(f"错误: {e}")
        return text


def add_shuiyin_suffix(video_path):
    if not has_shuiyin_suffix(video_path):
        base, ext = os.path.splitext(video_path)
        return f"{base}_shuiyin{ext}"
    return video_path


def add_zimu_suffix(video_path):
    if not has_zimu_suffix(video_path):
        base, ext = os.path.splitext(video_path)
        return f"{base}_zimu{ext}"
    return video_path


def has_shuiyin_suffix(video_path):
    return "_shuiyin" in os.path.basename(video_path)


def has_zimu_suffix(video_path):
    return "_zimu" in os.path.basename(video_path)


def get_relative_path(path, start=os.curdir):
    if os.path.isabs(path):
        return os.path.relpath(path, start).replace("\\", "/")
    return path.replace("\\", "/")


def replace_comma_with_newline(input_string):
    if ',' in input_string:
        return input_string.replace(',', '\n')
    return input_string


def get_path_without_suffix(path):
    # 使用os.path.basename获取文件名
    filename = os.path.basename(path)
    # 检查文件名是否包含下划线
    if '_' in filename:
        # 获取下划线前面的部分
        base_name = filename.split('_')[0]
        # 获取路径中的目录部分
        dir_name = os.path.dirname(path)
        # 返回拼接后的路径
        return os.path.join(dir_name, base_name)
    else:
        # 如果文件名不包含下划线，直接返回原路径
        return path


def process_srt(input_file_path: str) -> str:

    return input_file_path
