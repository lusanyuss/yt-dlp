import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from yuliu.utils import iso639_2_to_3, iso639_3_to_2


# 获取访问令牌
def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


# 翻译文本内容
def translate_text(text, target_language, source_language=None):
    access_token = get_access_token()
    url = "https://translation.googleapis.com/language/translate/v2"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": text, "target": target_language, "format": "text"}

    if source_language:
        params["source"] = source_language

    # 设置代理（如果需要）
    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }

    response = requests.post(url, headers=headers, params=params, proxies=proxies)
    response.raise_for_status()

    return response.json()['data']['translations'][0]['translatedText']


# 处理 SRT 文件并翻译内容
def translate_srt_file(path, target_language):
    print("===========================开始翻译字幕===========================")
    start_time = time.time()  # 记录开始时间

    source_language = os.path.splitext(path)[0].rsplit('_', 1)[-1]
    base_name = os.path.basename(path).rsplit('_', 1)[0]
    target_lang_code = iso639_2_to_3(target_language)
    new_file_name = f"{os.path.dirname(path)}/{base_name}_{target_lang_code}.srt"

    # 检查文件是否已经存在
    if os.path.exists(new_file_name):
        return new_file_name

    def read_lines(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                yield line

    translated_content = []
    text_to_translate = []
    text_blocks = []
    block_index = 0
    line_indices = []

    for i, line in enumerate(read_lines(path)):
        if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
            translated_content.append(line)
        elif line.strip() == "":
            if text_to_translate:
                text_blocks.append(" ".join(text_to_translate))
                line_indices.append(block_index)
                text_to_translate = []
            translated_content.append(line)
        else:
            text_to_translate.append(line.strip())
            translated_content.append(None)  # 占位符，用于稍后替换翻译文本
            block_index += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(translate_text, text, target_language, iso639_3_to_2(source_language)): index for index, text in enumerate(text_blocks)}

        translations = [None] * len(text_blocks)
        for future in as_completed(futures):
            index = futures[future]
            translations[index] = future.result() + '\n'

    translation_index = 0
    for i, line in enumerate(translated_content):
        if line is None and translation_index < len(translations):
            translated_content[i] = translations[translation_index]
            translation_index += 1

    # 移除原始中文文本行
    translated_content = [line for line in translated_content if line is not None]

    with open(new_file_name, 'w', encoding='utf-8') as file:
        file.writelines(translated_content)

    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算总耗时
    print(f"翻译字幕耗时{target_language}: {elapsed_time:.2f} 秒")  # 输出耗时

    return new_file_name


if __name__ == "__main__":
    source_file_path = 'release_video/aa测试目录/aa测试目录_cmn.srt'
    target_language = 'en'  # 翻译为英语
    new_srt_path = translate_srt_file(source_file_path, target_language)
    print(f"翻译后的 SRT 文件保存在: {new_srt_path}")
