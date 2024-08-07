import os
import re

import jieba
from opencc import OpenCC


def get_directory_and_mp4_names(directory):
    def remove_chinese_punctuation(text):
        return re.sub(r'[，。！？：（）《》【】]', '', text)

    def get_mod_time(entry_path):
        return os.path.getmtime(entry_path)

    entries = []

    for entry in os.listdir(directory):
        entry_path = os.path.join(directory, entry)
        mod_time = get_mod_time(entry_path)
        if os.path.isdir(entry_path) and not entry.startswith('.accelerate'):
            cleaned_name = entry
            if '-' in entry:
                cleaned_name = cleaned_name.split('-', 1)[1]
            if '（' in cleaned_name:
                cleaned_name = cleaned_name.split('（', 1)[0]
            cleaned_name = remove_chinese_punctuation(cleaned_name.strip())
            entries.append((cleaned_name, mod_time))
        elif os.path.isfile(entry_path) and entry.endswith('.mp4'):
            cleaned_name = remove_chinese_punctuation(entry[:-4])
            entries.append((cleaned_name, mod_time))

    # 按修改时间排序，从近到远
    entries.sort(key=lambda x: x[1], reverse=True)

    # 只保留名称
    sorted_names = [name for name, _ in entries]

    return sorted_names


def process_strings(data):
    # 初始化繁体到简体的转换器
    cc = OpenCC('t2s')
    # 去掉逗号并将繁体中文转换为简体中文
    cleaned_result = [cc.convert(item.replace(',', '')) for item in data]
    # 分词处理
    simplified_result = [''.join(jieba.cut(item)) for item in cleaned_result]

    return simplified_result


def get_valid_directories(base_dir):
    # 获取所有以xxx_ 前缀开头的目录
    pattern = re.compile(r'^\d+_')
    valid_directories = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and pattern.match(d)]
    # 使用下划线分割目录名称并获取第一个部分
    directory_numbers = [d.split('_')[1] for d in valid_directories]
    return directory_numbers


if __name__ == '__main__':
    directory_path = r'C:\download_short_film\baidu'
    result = get_directory_and_mp4_names(directory_path)
    print("现有资源集合:", result)

    # 读取文件内容
    with open('banned_list.sh', 'r', encoding='utf-8') as file:
        data = file.read()
    # 使用正则表达式提取单引号中的内容
    pattern = re.compile(r"'(.*?)'")
    banned_result = pattern.findall(data)
    # 处理提取的结果
    # release_video目录
    release_video_dir = os.path.join('./', 'release_video')
    # 获取有效的目录
    valid_dirs = list(set(process_strings(get_valid_directories(release_video_dir)) + process_strings(banned_result)))
    # print("已上架目录集合:", valid_dirs)

    # 将结果转换为集合
    result_set = set(result)
    valid_dirs_set = set(valid_dirs)

    # 找到已经上架和未上架的资源
    already_uploaded = sorted(result_set.intersection(valid_dirs_set), key=lambda x: result.index(x))
    not_uploaded = sorted(result_set.difference(valid_dirs_set), key=lambda x: result.index(x))

    print("\n\n已上架的资源:", already_uploaded)
    print(f"未上架的资源{len(not_uploaded)}:", not_uploaded)
