from opencc import OpenCC


def read_srt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def parse_srt(srt):
    subtitles = []
    blocks = srt.strip().split('\n\n')
    for block in blocks:
        lines = block.split('\n')
        index = int(lines[0])
        time_frame = lines[1]
        content = ' '.join(lines[2:])
        subtitles.append((index, time_frame, content))
    return subtitles


def check_duplicates(zh_srt_path):
    from collections import defaultdict

    # 读取并解析srt字幕文件
    zh_srt = read_srt_file(zh_srt_path)
    subtitles = parse_srt(zh_srt)

    # 检查异常情况
    content_indices = defaultdict(list)
    for sub in subtitles:
        content_indices[sub[2]].append(sub[0])

    # 检查并打印异常情况
    for content, indices in content_indices.items():
        if len(indices) > 5:
            for i in range(len(indices) - 5):
                if indices[i + 5] - indices[i] == 5:
                    raise Exception(f"异常: 内容 '{content}' 在以下索引中重复出现: {indices[i]} 到 {indices[i + 5]}")

    print("检查完成，没有发现异常")


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


if __name__ == '__main__':
    # 示例srt字幕内容
    # 示例用法
    zh_srt_path = '/yuliu/release_video/aa测试目录min/aa测试目录_zh.srt'
    check_duplicates(zh_srt_path)
