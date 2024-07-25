import os
import shutil


def get_src_folder(base_dir):
    src_folder = os.path.join(base_dir, 'src')
    if os.path.isdir(src_folder):
        return src_folder
    return None


def get_video_files(src_folder):
    video_files = [f for f in os.listdir(src_folder) if f.endswith(('.mp4', '.avi', '.mkv'))]
    return video_files


def move_and_rename_videos(base_dir, src_folder, video_files):
    for video in video_files:
        new_folder_name = os.path.splitext(video)[0]
        new_folder_path = os.path.join(base_dir, new_folder_name)
        new_video_path = os.path.join(new_folder_path, '1.mp4')

        # 如果文件夹已经存在且视频已被处理，跳过
        if os.path.exists(new_folder_path) and os.path.exists(new_video_path):
            print(f"Video {video} already processed, skipping.")
            continue

        # 创建新的文件夹
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)

        # 移动并重命名视频文件
        video_path = os.path.join(src_folder, video)
        shutil.move(video_path, new_video_path)
        # print(f"Video {video} moved to {new_folder_path} and renamed to 1.mp4.")
        print(f"'{video.rsplit('.', 1)[0]}',")

def get_filtered_folders(base_dir):
    filtered_folders = []

    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path) and folder != 'src' and '测试' not in folder:
            filtered_folders.append(folder)

    return filtered_folders


def main():
    base_dir = os.getcwd()
    src_folder = get_src_folder(base_dir)

    if src_folder:
        video_files = get_video_files(src_folder)
        move_and_rename_videos(base_dir, src_folder, video_files)
    else:
        print("No 'src' folder found in the current directory.")

    folders = get_filtered_folders(base_dir)
    print("\nFiltered folders:")
    for folder in folders:
        print(f"\'{folder}\',")

if __name__ == "__main__":
    main()
