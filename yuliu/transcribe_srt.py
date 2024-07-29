import os
import re
import time

import requests
import urllib3.exceptions
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from yuliu.utils import print_yellow

requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 全局变量
CREDENTIALS_PATH = 'yuliusecret-radiant-works-430523-c8-26198acdb648.json'
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
DEFAULT_MAX_PAYLOAD_SIZE = 1536  # 默认每次请求的最大负载大小（字节）

# 定义ISO 639-3到ISO 639-1的映射
iso639_3_to_2_map = {
    "eng": "en",
    "cmn": "zh",
    "spa": "es",
    "hin": "hi",
    "arb": "ar",
    "por": "pt",
    "fra": "fr",
    "deu": "de",
    "rus": "ru",
    "jpn": "ja"
}

# 创建一个反向映射从ISO 639-1到ISO 639-3
iso639_2_to_3_map = {v: k for k, v in iso639_3_to_2_map.items()}


def iso639_3_to_2(code):
    return iso639_3_to_2_map.get(code, code)


def iso639_2_to_3(code):
    return iso639_2_to_3_map.get(code, code)


def create_session_with_retries(retries, backoff_factor, status_forcelist):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_access_token():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        print(f"获取 access token 失败: {e}")
        return None


def translate_texts(params):
    url = "https://translation.googleapis.com/language/translate/v2"
    try:
        response = requests.post(url, data=params)
        if response.status_code == 200:
            data = response.json()
            translations = data.get('data', {}).get('translations', [])
            return [t['translatedText'] for t in translations]
        else:
            print(f"Error {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    return []


def translate_text_batch(texts, target_language, source_language=None, max_payload_size=DEFAULT_MAX_PAYLOAD_SIZE):
    all_translations = []
    total_requests = 0
    current_length = 0

    for text in texts:
        text_length = len(text.encode('utf-8'))
        if current_length + text_length + len(texts) * 2 > max_payload_size:
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
        if current_length + text_length + len(current_texts) * 2 > max_payload_size:
            params = {
                'key': os.environ['GOOGLE_API_KEY'],
                "q": current_texts,
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
            "target": target_language,
            "format": "text"
        }
        translations = translate_texts(params)
        all_translations.extend(translations)

    return all_translations


def translate_srt_file(zimu_srt, target_language, max_payload_size=DEFAULT_MAX_PAYLOAD_SIZE):
    if not os.path.exists(zimu_srt):
        raise Exception("中文字幕不存在")

    print("===========================开始翻译字幕===========================")
    start_time = time.time()

    source_language = os.path.splitext(zimu_srt)[0].rsplit('_', 1)[-1]
    base_name = os.path.basename(zimu_srt).rsplit('_', 1)[0]
    target_lang_code = iso639_2_to_3(target_language)
    new_file_name = f"{os.path.dirname(zimu_srt)}/{base_name}_{target_lang_code}.srt"

    if os.path.exists(new_file_name):
        print(f"{new_file_name}字幕存在,缓存返回")
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
        translations = translate_text_batch(text_blocks, iso639_3_to_2(target_language), iso639_3_to_2(source_language), max_payload_size)
        for i, block_index in enumerate(block_indices):
            translated_content[block_index] = translations[i] + '\n'

    translated_content = [line if line is not None else '' for line in translated_content]

    with open(new_file_name, 'w', encoding='utf-8') as file:
        file.writelines(translated_content)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"翻译字幕耗时{target_language}: {elapsed_time:.2f} 秒")

    return new_file_name


if __name__ == "__main__":
    source_file_path = 'release_video/aa测试目录/aa测试目录_cmn_corrected.srt'
    traget_file_path = 'release_video/aa测试目录/aa测试目录_eng.srt'

    if os.path.exists(traget_file_path):
        os.remove(traget_file_path)

    target_language = 'en'
    new_srt_path = translate_srt_file(source_file_path, target_language, max_payload_size=2048)
    print(f"翻译后的 SRT 文件保存在: {new_srt_path}")
