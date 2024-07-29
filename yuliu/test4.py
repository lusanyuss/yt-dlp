import os

import requests


def translate_text(text_list, target_language='en'):
    url = 'https://translation.googleapis.com/language/translate/v2'

    params = {
        'key': os.environ['GOOGLE_API_KEY'],
        'q': text_list,
        'target': target_language,
        'format': 'text'
    }

    response = requests.post(url, data=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error {response.status_code}: {response.text}')
        return None


# 示例数据
texts_to_translate = [
    '这是我的妹妹沈莉莉', '因为生得好看', '成了知名歌星', '知名歌星沈莉莉的单曲',
    '听不见的声音', '上线一小时', '付费量破亿', '是目前华国乐坛史上最好成绩',
    '大惊小怪', '但她并不会唱歌', '这个丑陋无比的人', '是我沈芸', '天生拥有一副好嗓音',
    '却只能做妹妹沈莉莉的替唱', '一张丑脸有什么好遮挡的', '一会到了公司',
    '看见记者直接推开', '知道吗', '每次都离那么近', '身上汗味熏死我了',
    '他们也只是打工的', '没必要吧', '闭嘴', '臭八怪', '丑八怪敢性逆我',
    '把你赶出沈家', '把你赶出沈家', '大家快看', '沈莉莉小姐来了',
    '周A88888', '莉莉小姐', '莉莉小姐', '挡死'
]

result_json = translate_text(texts_to_translate)
print(result_json)
