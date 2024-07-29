import os
import subprocess
import time
from multiprocessing import Pool


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def split_video(input_video, output_dir, segment_length=600):
    create_directory(output_dir)
    command = [
        'ffmpeg', '-i', input_video, '-c', 'copy', '-map', '0',
        '-segment_time', str(segment_length), '-f', 'segment',
        '-reset_timestamps', '1', os.path.join(output_dir, 'part%02d.mp4')
    ]
    subprocess.run(command, check=True)


def process_segment(segment, x):
    segment_path, output_dir = segment
    segment_name = os.path.basename(segment_path).split('.')[0]
    output_path = os.path.join(output_dir, segment_name)
    create_directory(output_path)

    # Calculate Y coordinates based on the given formula
    video_height = 1920  # 假设视频高度为1920
    y_start = int((75 - x) % 100 * video_height / 100)
    y_end = int((75 + x) % 100 * video_height / 100)
    crop_height = y_end - y_start

    # Extract frames with fps and crop filter based on calculated Y coordinates
    command = [
        'ffmpeg', '-i', segment_path,
        f'-vf', f'fps=2,crop=in_w:{crop_height}:0:{y_start}',
        os.path.join(output_path, 'frame_%04d.jpg')
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Log output and errors
    with open('ffmpeg_output.log', 'a') as log_file:
        log_file.write(result.stdout)
        log_file.write(result.stderr)

    result.check_returncode()
    return output_path


def process_video(input_video, x, num_processes=6):
    # Step 1: Split video into segments
    output_dir = os.path.dirname(input_video)
    split_dir = os.path.join(output_dir, 'segments')
    split_video(input_video, split_dir)

    # Step 2: Process each segment in parallel
    segments = [(os.path.join(split_dir, f), output_dir) for f in os.listdir(split_dir)]
    with Pool(processes=num_processes) as pool:
        result_dirs = pool.starmap(process_segment, [(segment, x) for segment in segments])

    return result_dirs


if __name__ == "__main__":
    start_time = time.time()  # 记录开始时间

    input_video = "release_video/test_long/video2hour.mp4"
    x = 8  # 设置x的值
    num_processes = 12  # 设置并行进程数量

    result_directories = process_video(input_video, x, num_processes)

    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算耗时

    # print("截图已保存到以下目录：")
    # for directory in result_directories:
    #     print(directory)

    print(f"代码执行耗时：{elapsed_time:.2f} 秒")
