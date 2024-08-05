import os
import re
import shutil
import time

from yuliu.utils import concatenate_folder_videos


def get_aasrc_folder(base_dir):
    aasrc_folder = os.path.join(base_dir, 'aasrc')
    if os.path.isdir(aasrc_folder):
        return aasrc_folder
    return None


def get_video_files(aasrc_folder):
    video_files = [f for f in os.listdir(aasrc_folder) if f.endswith(('.mp4', '.avi', '.mkv'))]
    return video_files


def move_and_rename_videos(base_dir, aasrc_folder, video_files):
    max_number, name_list = get_max_prefix_number_and_names()
    print(f"最大前缀数字: {max_number}")
    print("所有名称列表: ", name_list)
    print("\n\n")

    current_number = max_number + 1

    for video in video_files:
        video_name = os.path.splitext(video)[0]
        new_folder_path = os.path.join(base_dir, f"{current_number:03d}_{video_name}")
        new_video_path = os.path.join(new_folder_path, f"{video_name}.mp4")

        # 如果文件夹已经存在且视频已被处理，跳过
        if video_name in name_list:
            print(f"Video {video} already processed, skipping.")
            continue

        # 创建新的文件夹
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)

        # 移动并重命名视频文件
        video_path = os.path.join(aasrc_folder, video)
        shutil.move(video_path, new_video_path)
        print(f"'{video.rsplit('.', 1)[0]}',")

        # 增加当前索引
        current_number += 1


def get_filtered_folders(base_dir):
    filtered_folders = []

    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path) and folder != 'aasrc' and '测试' not in folder:
            filtered_folders.append(folder)

    return filtered_folders


def get_all_directories(base_dir):
    exclude_dirs = {'__pycache__'}
    return [os.path.join(base_dir, name) for name in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, name)) and name not in exclude_dirs]


def get_max_prefix_number_and_names():
    # 获取当前目录的上一级目录
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))

    # 获取上一级目录中所有以 xxx_ 前缀开头的目录
    pattern = re.compile(r'^(\d{3})_(.+)')
    max_number = 0
    name_list = []

    for d in os.listdir(parent_dir):
        if os.path.isdir(os.path.join(parent_dir, d)):
            match = pattern.match(d)
            if match:
                number = int(match.group(1))
                name = match.group(2)
                name_list.append(name)
                if number > max_number:
                    max_number = number

    return max_number, name_list


if __name__ == "__main__":

    base_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    aasrc_folder = os.getcwd()
    max_number, name_list = get_max_prefix_number_and_names()

    for folder in get_all_directories(aasrc_folder):
        start_time = time.time()
        if os.path.basename(folder) not in name_list:
            final_video = concatenate_folder_videos(folder)
            print(f"视频合并消耗的时间: {time.time() - start_time:.2f} 秒")
        else:
            print(f"{folder} 已经存在")
    if aasrc_folder:
        video_files = get_video_files(aasrc_folder)
        move_and_rename_videos(base_dir, aasrc_folder, video_files)
    else:
        print("No 'aasrc' folder found in the current directory.")
