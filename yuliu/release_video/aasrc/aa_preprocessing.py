import os
import re
import shutil
import time

from yuliu.utils import concatenate_folder_videos, print_red


def get_aasrc_folder(base_dir):
    aasrc_folder = os.path.join(base_dir, 'aasrc')
    return aasrc_folder if os.path.isdir(aasrc_folder) else None


def get_video_files(aasrc_folder):
    return [f for f in os.listdir(aasrc_folder) if f.endswith(('.mp4', '.avi', '.mkv'))]


def move_and_rename_videos(base_dir, aasrc_folder, video_files):
    max_number, name_list = get_max_prefix_number_and_names()
    print(f"最大前缀数字: {max_number}")
    print("所有名称列表: ", name_list, "\n\n")

    current_number = max_number + 1

    for video in video_files:
        video_name = os.path.splitext(video)[0]
        new_folder_path = os.path.join(base_dir, f"{current_number:03d}_{video_name}")
        new_video_path = os.path.join(new_folder_path, f"{video_name}.mp4")

        if video_name in name_list:
            print(f"视频 {video} 已处理，跳过。")
            continue

        os.makedirs(new_folder_path, exist_ok=True)
        shutil.move(os.path.join(aasrc_folder, video), new_video_path)
        print(f"'{video_name}',")

        current_number += 1


def get_filtered_folders(base_dir):
    return [folder for folder in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, folder)) and folder != 'aasrc' and '测试' not in folder]


def get_all_directories(base_dir):
    exclude_dirs = {'__pycache__'}
    return [os.path.join(base_dir, name) for name in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, name)) and name not in exclude_dirs]


def get_max_prefix_number_and_names():
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    pattern = re.compile(r'^(\d{3})_(.+)')
    max_number = 0
    name_list = []

    for d in os.listdir(parent_dir):
        match = pattern.match(d)
        if match:
            number = int(match.group(1))
            name = match.group(2)
            name_list.append(name)
            max_number = max(max_number, number)

    return max_number, name_list


def clean_and_check_folder(folder):
    try:
        files = os.listdir(folder)
    except Exception as e:
        print(f"无法列出目录中的文件: {e}")
        return False

    for f in files:
        if not f.lower().endswith('.mp4') or re.search(r'\.(jpg|jpeg|png|gif|webp)$', f, re.IGNORECASE):
            try:
                os.remove(os.path.join(folder, f))
            except Exception as e:
                print(f"无法删除文件 {f}: {e}")

    for f in files:
        if '..' in f:
            try:
                os.rename(os.path.join(folder, f), os.path.join(folder, f.replace('..', '.')))
            except Exception as e:
                print(f"无法重命名文件 {f}: {e}")

    try:
        mp4_files = [f for f in os.listdir(folder) if f.lower().endswith('.mp4')]
    except Exception as e:
        print(f"无法获取目录中的 mp4 文件: {e}")
        return False

    pattern = re.compile(r'^(\d+)\.mp4$')
    numbers = [int(match.group(1)) for f in mp4_files if (match := pattern.match(f))]

    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        print("文件命名不连续")
        return False

    return True


def remove_chinese_punctuation(text):
    return re.sub(r'[，。！？：（）《》【】]', '', text)


def rename_directories(directory):
    for entry in os.listdir(directory):
        entry_path = os.path.join(directory, entry)
        if os.path.isdir(entry_path) and not entry.startswith('.accelerate'):
            cleaned_name = remove_chinese_punctuation(entry.split('-', 1)[-1].split('（', 1)[0].strip())
            new_path = os.path.join(directory, cleaned_name)
            try:
                os.rename(entry_path, new_path)
            except Exception as e:
                print(f"无法重命名目录 {entry_path} 为 {new_path}: {e}")


if __name__ == "__main__":
    with open('../../banned_list.sh', 'r', encoding='utf-8') as file:
        data = file.read()

    pattern = re.compile(r"'(.*?)'")
    result = pattern.findall(data)

    base_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    aasrc_folder = os.getcwd()
    max_number, name_list = get_max_prefix_number_and_names()
    result.extend(name_list)

    rename_directories(aasrc_folder)

    for folder in get_all_directories(aasrc_folder):
        if clean_and_check_folder(folder):
            print("目录合格，继续执行")
            start_time = time.time()
            if os.path.basename(folder) not in result:
                final_video = concatenate_folder_videos(folder)
                print(f"视频合并消耗的时间: {time.time() - start_time:.2f} 秒")
            else:
                print_red(f"{folder} 已经存在")
        else:
            print_red("目录不合格，停止执行")
            exit()

    if aasrc_folder:
        video_files = get_video_files(aasrc_folder)
        move_and_rename_videos(base_dir, aasrc_folder, video_files)
    else:
        print_red("未找到 'aasrc' 文件夹。")
