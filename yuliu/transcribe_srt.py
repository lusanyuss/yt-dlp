import os
import re
import time
import traceback

import requests
import urllib3.exceptions
from requests.packages.urllib3.util.retry import Retry

from yuliu.utils import print_yellow

requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CREDENTIALS_PATH = 'yuliusecret-radiant-works-430523-c8-26198acdb648.json'
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

language_map = {
    "en": "英语",
    "es": "西班牙语",
    "hi": "印地语",
    "ar": "阿拉伯语",
    "pt": "葡萄牙语",
    "fr": "法语",
    "de": "德语",
    "ja": "日语",
    "ko": "韩语",
    "zh-TW": "台湾繁体",
    "zh": "中文简体"
}


def translate_texts(params, retries=5, delay=2):
    url = "https://translation.googleapis.com/language/translate/v2"
    print("请求参数: ", params)
    for attempt in range(retries):
        try:
            if 'q' in params:
                q_length = len(params['q'])
                q_byte_size = calculate_total_byte_size(params['q'])
                print(f"q 的长度: {q_length}, q 的字节大小: {q_byte_size}")

            response = requests.post(url, data=params, proxies=PROXIES, verify=False)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'translations' in data['data']:
                    translations = data['data']['translations']
                    if translations:
                        return [t['translatedText'] for t in translations]
                    else:
                        print("Translations list is empty.")
                else:
                    print("Unexpected response structure:", data)
            else:
                print(f"Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")

        if attempt < retries - 1:
            time.sleep(delay)
            print(f"Retrying... (attempt {attempt + 2}/{retries})")

    print("All attempts failed.")
    return []


def calculate_total_byte_size(texts, encoding='utf-8'):
    total_size = 0
    for text in texts:
        total_size += len(text.encode(encoding))
    return total_size


def translate_text_batch(texts, target_language, max_payload_size):
    all_translations = []
    total_requests = 0
    current_length = 0

    try:
        for text in texts:
            text_length = len(text.encode('utf-8'))
            if current_length + text_length > max_payload_size:
                total_requests += 1
                current_length = 0
            current_length += text_length

        if current_length > 0:
            total_requests += 1

        print(f"根据 max_payload_size = {max_payload_size}，一共需要请求 {total_requests} 次翻译")

        current_texts = []
        current_length = 0

        for text in texts:
            text_length = len(text.encode('utf-8'))
            if current_length + text_length > max_payload_size:
                params = {
                    'key': os.environ['GOOGLE_API_KEY'],
                    "q": current_texts,
                    'source': 'zh-CN',
                    "target": target_language,
                    "format": "text"
                }
                translations = translate_texts(params)
                all_translations.extend(translations)

                current_texts = []
                current_length = 0

            current_texts.append(text)
            current_length += text_length

        if current_texts:
            params = {
                'key': os.environ['GOOGLE_API_KEY'],
                "q": current_texts,
                'source': 'zh-CN',
                "target": target_language,
                "format": "text"
            }
            translations = translate_texts(params)
            all_translations.extend(translations)
    except Exception as e:
        print("出错:", str(e))
        traceback.print_exc()

    return all_translations


def translate_srt_file(zimu_srt, target_language, max_payload_size):
    try:
        if not os.path.exists(zimu_srt):
            raise Exception("中文字幕不存在")

        print(f"===========================开始翻译字幕 {target_language}===========================")
        start_time = time.time()

        source_language = os.path.splitext(zimu_srt)[0].rsplit('_', 1)[-1]
        base_name = os.path.basename(zimu_srt).rsplit('_', 1)[0]
        new_file_name = f"{os.path.dirname(zimu_srt)}/{base_name}_{language_map[target_language]}.srt"
        new_file_name_code = f"{os.path.dirname(zimu_srt)}/{base_name}_{target_language}.srt"
        if os.path.exists(new_file_name_code):
            os.replace(new_file_name_code, new_file_name)
        if os.path.exists(new_file_name):
            print_yellow(f"{new_file_name}字幕存在,缓存返回")
            return new_file_name

        def read_lines(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    yield line

        translated_content = []
        text_blocks = []
        block_indices = []
        current_block = []
        current_block_size = 0

        for line in read_lines(zimu_srt):
            if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
                translated_content.append(line)
            elif line.strip() == "":
                if current_block:
                    text_blocks.append("\n".join(current_block))
                    block_indices.append(len(translated_content) - len(current_block))
                    current_block = []
                    current_block_size = 0
                translated_content.append(line)
            else:
                line_size = len(line.strip().encode('utf-8'))
                if current_block_size + line_size > max_payload_size:
                    text_blocks.append("\n".join(current_block))
                    block_indices.append(len(translated_content) - len(current_block))
                    current_block = [line.strip()]
                    current_block_size = line_size
                else:
                    current_block.append(line.strip())
                    current_block_size += line_size
                translated_content.append(None)

        if current_block:
            text_blocks.append("\n".join(current_block))
            block_indices.append(len(translated_content) - len(current_block))

        if text_blocks:
            translations = translate_text_batch(text_blocks, target_language, max_payload_size)
            if len(translations) != len(block_indices):
                print("错误: translations 的长度和 block_indices 的长度不匹配")
                print(f"translations: {len(translations)}, block_indices: {len(block_indices)}")
                return
            else:
                print_yellow("成功: translations 的长度和 block_indices 的长度一致")

            for i, block_index in enumerate(block_indices):
                translated_content[block_index] = translations[i] + '\n'

        translated_content = [line if line is not None else '' for line in translated_content]

        with open(new_file_name, 'w', encoding='utf-8') as file:
            file.writelines(translated_content)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print_yellow(f"翻译{language_map[target_language]}字幕成功! 耗时: {elapsed_time:.2f} 秒")

        return new_file_name
    except Exception as e:
        print("出错:", str(e))
        traceback.print_exc()


if __name__ == "__main__":
    source_file_path = 'release_video/aa测试目录/aa测试目录_zh.srt'
    target_file_path = 'release_video/aa测试目录/aa测试目录_en.srt'

    if os.path.exists(target_file_path):
        os.remove(target_file_path)

    target_language = 'en'
    new_srt_path = translate_srt_file(source_file_path, target_language, max_payload_size=256)
    print(f"翻译后的 SRT 文件保存在: {new_srt_path}")
