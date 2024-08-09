import os
import re
import shutil


def get_dir(base_dir, sub_directory=None):
    dir_path = os.path.join(os.getcwd(), base_dir)
    if sub_directory:
        dir_path = os.path.join(dir_path, sub_directory)
    return dir_path


def delete_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"已删除文件夹及其内容: {directory}")
    else:
        print(f"文件夹不存在: {directory}")


def get_name_to_number_mapping():
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), 'release_video'))
    pattern = re.compile(r'^(\d{3})_(.+)')
    name_mapping = {}

    for d in os.listdir(parent_dir):
        match = pattern.match(d)
        if match:
            name = match.group(2)
            number_name = match.group(0)
            name_mapping[name] = number_name

    return name_mapping


if __name__ == '__main__':

    name_mapping = get_name_to_number_mapping()
    with open('banned_list.sh', 'r', encoding='utf-8') as file:
        data = file.read()
    pattern = re.compile(r"'(.*?)'")
    video_name_list = pattern.findall(data)
    base_dirs = [
        # "release_video",
        os.path.join("MVSEP-MDX23-Colab_v2", "input"),
        os.path.join("MVSEP-MDX23-Colab_v2", "output")
    ]

    for video_name in video_name_list:
        if video_name in name_mapping:
            video_path = f'release_video/{name_mapping[video_name]}'

            video_path_input = os.path.join("MVSEP-MDX23-Colab_v2", "input", f"{name_mapping[video_name]}")
            delete_dir(video_path_input)

            video_path_output = os.path.join("MVSEP-MDX23-Colab_v2", "output", f"{name_mapping[video_name]}")
            delete_dir(video_path_output)

            video_path_image = f'{video_path}/images'
            # 要保留的文件名列表
            if os.path.exists(video_path_image):
                keep_files = {'1.jpg', '2.jpg', '3.jpg', 'input_img123.png'}
                # 删除不在保留列表中的文件
                for filename in os.listdir(video_path_image):
                    if filename not in keep_files:
                        os.remove(os.path.join(video_path_image, filename))

            video_path_offset = f'{video_path}/offset'
            delete_dir(video_path_offset)

            video_path_out_times = f'{video_path}/out_times'
            delete_dir(video_path_out_times)

            video_path_nobgm = f'{video_path}/{video_name}_nobgm.mp4'
            video_path_nobgm_final = f'{video_path}/{video_name}_nobgm_final.mp4'
            # 如果两个文件都存在，删除 video_path_nobgm_final
            if os.path.exists(video_path_nobgm) and os.path.exists(video_path_nobgm_final):
                os.remove(video_path_nobgm_final)

            # for base_dir in base_dirs:
            #     dir_path = get_dir(base_dir, sub_directory)
            #     delete_dir(dir_path)
