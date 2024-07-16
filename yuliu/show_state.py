import os


def get_filtered_directories(base_directory, exclude_dirs):
    all_dirs = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    filtered_dirs = []

    for d in all_dirs:
        if d not in exclude_dirs:
            dir_path = os.path.join(base_directory, d)
            mp4_files = [f for f in os.listdir(dir_path) if f.endswith('.mp4')]
            if f"{d}.mp4" in mp4_files:
                filtered_dirs.append(d)

    return filtered_dirs


def get_filtered_input_directories(base_directory, exclude_dirs):
    all_dirs = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    filtered_dirs = [d for d in all_dirs if d not in exclude_dirs]

    final_dirs = []
    for d in filtered_dirs:
        dir_path = os.path.join(base_directory, d)
        if '1.mp4' in os.listdir(dir_path):
            final_dirs.append(d)

    return final_dirs


def get_filtered_output_directories(base_directory, exclude_dirs):
    all_dirs = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    filtered_dirs = []

    for d in all_dirs:
        if d not in exclude_dirs:
            dir_path = os.path.join(base_directory, d)
            mp4_files = [f for f in os.listdir(dir_path) if f.endswith('.mp4')]
            if f"{d}.mp4" in mp4_files:
                filtered_dirs.append(d)

    return filtered_dirs


if __name__ == '__main__':
    download_cache = os.path.join(os.getcwd(), 'download_cache')
    release_video = os.path.join(os.getcwd(), 'release_video')
    exclude_dirs = {'src', 'aa测试目录'}
    # 获取过滤后的文件夹列表
    download_cache_directories = get_filtered_input_directories(download_cache, exclude_dirs)
    release_video_directories = get_filtered_output_directories(release_video, exclude_dirs)

    # Create a set for faster lookup
    release_set = set(release_video_directories)

    # Prepare data for tabulation
    data = []
    for item in download_cache_directories:
        release_item = item if item in release_set else ""
        data.append([item, release_item])

    # Add release_video_directories items that are not in download_cache_directories
    for item in release_video_directories:
        if item not in download_cache_directories:
            data.append(["", item])

    # Define fixed column width
    col_width = 40

    # Print header for the main table
    header = f"{'源头视频':<{col_width}}\t{'发布视频':<{col_width}}"
    separator = "-" * (col_width * 2 + 8)
    print(header)
    print(separator)

    # Print rows for the main table
    for row in data:
        print(f"{row[0]:<{col_width}}\t{row[1]:<{col_width}}")

    # Prepare data for the secondary table (items with empty release directory)
    empty_release_data = [row[0] for row in data if row[1] == ""]

    if empty_release_data:
        # Print header for the secondary table
        print("\n下载缓存文件夹对应的发布文件夹为空的数据:")
        print("-" * col_width)
        for item in empty_release_data:
            print(f"{item:<{col_width}}")
        print("-" * col_width)
