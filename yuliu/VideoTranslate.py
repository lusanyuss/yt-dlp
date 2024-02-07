from googletrans import Translator
from translate import Translator


def translate_to_chinese(text, source_language):
    translator = Translator(from_lang=source_language, to_lang="zh")
    translation = translator.translate(text)
    return translation
# 示例使用
# text_english = "Hello World"
# text_korean = "안녕하세요"
#
# translated_text_english = translate_to_chinese(text_english, "en")
# translated_text_korean = translate_to_chinese(text_korean, "ko")
#
# print(translated_text_english)
# print(translated_text_korean)


def split_text(query, max_length=13000):
    """将文本分割为不超过最大长度的多个段。"""
    segments = []
    while len(query) > max_length:
        segment_pos = query[max_length:].find('\n')

        # 如果没有找到新行，则使用最大长度
        if segment_pos == -1:
            segment_pos = max_length
        else:
            segment_pos += max_length

        segments.append(query[:segment_pos])
        query = query[segment_pos:]

    if query:  # 添加剩余的文本
        segments.append(query)

    return segments


def translate_text(text, source_language):
    """使用Google Translate翻译文本。"""
    translator = Translator(from_lang=source_language, to_lang="zh")
    # 将文本分割为适当的段
    query_segments = split_text(text)
    # 开始翻译
    try:
        translated_segments = [res.text for res in
                               translator.translate(query_segments)]
        return ''.join(translated_segments)
    except Exception as e:
        print(f"翻译错误: {e}")
        return None
