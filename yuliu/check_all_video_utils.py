import os

import jieba


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


import re
from opencc import OpenCC


def convert_to_simplified_and_save(filename):
    # 初始化转换器，将繁体转换为简体
    cc = OpenCC('tw2sp')

    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        data = file.read()

    # 将文件内容转换为简体中文
    data_simplified = cc.convert(data)

    # 使用正则表达式匹配单引号内的内容
    pattern = re.compile(r"'(.*?)'")
    matches = pattern.findall(data_simplified)

    # 去重并保持原有顺序
    unique_matches = list(dict.fromkeys(matches))

    # 将去重后的内容重新组装回文件内容
    data_unique = ',\n'.join([f"'{item}'" for item in unique_matches])

    # 将去重后的简体中文内容写回文件，覆盖旧版本
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data_unique)


if __name__ == '__main__':
    directory_path = r'C:\download_short_film\baidu'
    result = get_directory_and_mp4_names(directory_path)
    print("百度网盘集合:\n", result)
    # 转换繁体,并去重
    convert_to_simplified_and_save('banned_list.sh')
    with open('banned_list.sh', 'r', encoding='utf-8') as file:
        data = file.read()
    pattern = re.compile(r"'(.*?)'")
    banned_result = pattern.findall(data)
    # 处理提取的结果
    # release_video目录
    release_video_dir = os.path.join('./', 'release_video')
    # 获取有效的目录
    valid_dirs = list(set(process_strings(get_valid_directories(release_video_dir)) + process_strings(banned_result)))

    # 将结果转换为集合
    result_set = set(result)
    valid_dirs_set = set(valid_dirs)

    # 找到已经上架和未上架的资源
    already_uploaded = sorted(result_set.intersection(valid_dirs_set), key=lambda x: result.index(x))
    not_uploaded = sorted(result_set.difference(valid_dirs_set), key=lambda x: result.index(x))

    print("\n\nYoutube已上架的资源:\n", already_uploaded)
    print(f"\n\n未上架的资源{len(not_uploaded)}:\n", not_uploaded)
