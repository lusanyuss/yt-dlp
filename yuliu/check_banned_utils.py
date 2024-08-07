import os
import re

from opencc import OpenCC

from yuliu.utils import print_red


def convert_simplified_to_traditional(text):
    try:
        cc = OpenCC('s2t')
        return cc.convert(text)
    except Exception:
        return text


def read_banned_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去掉每一行的多余字符，并忽略空行
    banned_list = [line.strip().strip("',").strip("'") for line in lines if line.strip().strip("',").strip("'")]
    return banned_list


# 示例调用
def is_banned(title):
    banned_list = read_banned_list('banned_list.sh')
    traditional_title = convert_simplified_to_traditional(title)
    return title in banned_list or traditional_title in banned_list


def get_release_video_list():
    # 获取当前目录的上一级目录
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), 'release_video'))
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


if __name__ == '__main__':
    # 示例srt字幕内容
    # 示例用法
    max_number, name_list = get_release_video_list()

    banned_videos = []
    uploadable_videos = []

    for video_name in name_list:
        if is_banned(video_name):
            banned_videos.append(video_name)
        else:
            uploadable_videos.append(video_name)


    def format_video_list(video_list, columns=3, column_width=30):
        rows = [video_list[i:i + columns] for i in range(0, len(video_list), columns)]
        formatted_list = ""
        for row in rows:
            line = "｜".join(video.ljust(column_width, '　') for video in row)
            formatted_list += f"{line}\n"
        return formatted_list


    print("已上传的视频 (总数: {}):".format(len(banned_videos)))
    print_red(format_video_list(banned_videos))

    print("\n未上传的视频 (总数: {}):".format(len(uploadable_videos)))
    print(format_video_list(uploadable_videos))




