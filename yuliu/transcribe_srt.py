import os
import re
import time

import requests
import urllib3.exceptions
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 全局变量
CREDENTIALS_PATH = 'yuliusecret-radiant-works-430523-c8-26198acdb648.json'
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
DEFAULT_MAX_PAYLOAD_SIZE = 2048  # 默认每次请求的最大负载大小（字节）

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


# 定义方法从ISO 639-3转换到ISO 639-1
def iso639_3_to_2(code):
    if code in iso639_3_to_2_map:
        return iso639_3_to_2_map[code]
    return code


def iso639_2_to_3(code):
    if code in iso639_2_to_3_map:
        return iso639_2_to_3_map[code]
    return code


# 创建带有重试机制的 session
def create_session_with_retries(retries, backoff_factor, status_forcelist):
    try:
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
    except Exception as e:
        print(f"创建会话失败: {e}")
        return None


# 获取访问令牌
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


# 批量翻译文本内容
def translate_text_batch(texts, target_language, source_language=None, max_payload_size=DEFAULT_MAX_PAYLOAD_SIZE):
    access_token = get_access_token()
    if not access_token:
        print("未能获取 access token")
        return []

    url = "https://translation.googleapis.com/language/translate/v2"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_translations = []
    session = create_session_with_retries(retries=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

    if not session:
        print("未能创建会话")
        return []

    # 计算总请求次数
    total_requests = 0
    current_length = 0
    for text in texts:
        text_length = len(text.encode('utf-8'))
        if current_length + text_length + len(texts) * 2 > max_payload_size:
            total_requests += 1
            current_length = 0
        current_length += text_length

    # 最后一批文本也算一次请求
    if current_length > 0:
        total_requests += 1

    # 打印总请求次数
    print(f"根据 max_payload_size = {max_payload_size}，一共需要请求 {total_requests} 次翻译")

    # 分割文本块，确保每个请求的数据不超过限制
    current_texts = []
    current_length = 0
    for text in texts:
        text_length = len(text.encode('utf-8'))  # 计算UTF-8编码的字节长度
        if current_length + text_length + len(current_texts) * 2 > max_payload_size:
            # 打印日志
            print(f"翻译请求数据长度: {current_length} 字节")
            print(f"请求内容: {current_texts}")

            # 执行请求
            data = {
                "q": current_texts,
                "target": target_language,
                "format": "text"
            }
            if source_language:
                data["source"] = source_language
            try:
                response = session.post(url, headers=headers, json=data, proxies=PROXIES, verify=False)
                response.raise_for_status()
                translations = response.json()['data']['translations']
                all_translations.extend([t['translatedText'] for t in translations])
            except requests.exceptions.RequestException as e:
                print(f"请求失败: {e}")
                print(f"请求内容: {data}")
                print(f"响应内容: {response.text if response else '无响应'}")

            # 重置
            current_texts = []
            current_length = 0

        current_texts.append(text)
        current_length += text_length

    # 处理最后一批文本
    if current_texts:
        # 打印日志
        print(f"翻译请求数据长度: {current_length} 字节")
        print(f"请求内容: {current_texts}")

        data = {
            "q": current_texts,
            "target": target_language,
            "format": "text"
        }
        if source_language:
            data["source"] = source_language
        try:
            response = session.post(url, headers=headers, json=data, proxies=PROXIES, verify=False)
            response.raise_for_status()
            translations = response.json()['data']['translations']
            all_translations.extend([t['translatedText'] for t in translations])
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            print(f"请求内容: {data}")
            print(f"响应内容: {response.text if response else '无响应'}")

    return all_translations


# 处理 SRT 文件并翻译内容
def translate_srt_file(zimu_srt, target_language, max_payload_size=DEFAULT_MAX_PAYLOAD_SIZE):
    if not os.path.exists(zimu_srt):
        raise Exception("中文字幕不存在")

    print("===========================开始翻译字幕===========================")
    start_time = time.time()  # 记录开始时间

    source_language = os.path.splitext(zimu_srt)[0].rsplit('_', 1)[-1]
    base_name = os.path.basename(zimu_srt).rsplit('_', 1)[0]
    target_lang_code = iso639_2_to_3(target_language)
    new_file_name = f"{os.path.dirname(zimu_srt)}/{base_name}_{target_lang_code}.srt"

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
            translated_content.append(None)  # 占位符，用于稍后替换翻译文本

    if current_block:
        text_blocks.append("\n".join(current_block))
        block_indices.append(len(translated_content) - len(current_block))

    if text_blocks:
        translations = translate_text_batch(text_blocks, iso639_3_to_2(target_language), iso639_3_to_2(source_language), max_payload_size)

        for i, block_index in enumerate(block_indices):
            translated_content[block_index] = translations[i] + '\n'

    # 移除所有 None 值，确保写入文件时没有 None
    translated_content = [line if line is not None else '' for line in translated_content]

    with open(new_file_name, 'w', encoding='utf-8') as file:
        file.writelines(translated_content)

    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算总耗时
    print(f"翻译字幕耗时{target_language}: {elapsed_time:.2f} 秒")  # 输出耗时

    return new_file_name


if __name__ == "__main__":
    # source_file_path = 'release_video/豪门狂少归来/豪门狂少归来_cmn.srt'
    # traget_file_path = 'release_video/豪门狂少归来/豪门狂少归来_eng.srt'

    source_file_path = 'release_video/aa测试目录/aa测试目录_cmn.srt'
    traget_file_path = 'release_video/aa测试目录/aa测试目录_eng.srt'

    if os.path.exists(traget_file_path):
        os.remove(traget_file_path)

    target_language = 'en'  # 翻译为英语
    new_srt_path = translate_srt_file(source_file_path, target_language, max_payload_size=2048)
    print(f"翻译后的 SRT 文件保存在: {new_srt_path}")
