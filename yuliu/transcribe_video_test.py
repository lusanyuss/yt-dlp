from googletrans import Translator


def translate_text(text, dest='en'):
    translator = Translator()
    # 翻译文本到指定语言
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception as e:
        print(f"发生错误: {e}")
        return None

# 示例使用
translated_text_en = translate_text('你好，世界', 'en')
if translated_text_en:
    print(f"翻译结果 (英文): {translated_text_en}")  # => Hello, world

translated_text_jp = translate_text('你好，世界', 'ja')
if translated_text_jp:
    print(f"翻译结果 (日文): {translated_text_jp}")  # => こんにちは、世界

translated_text_fr = translate_text('你好，世界', 'fr')
if translated_text_fr:
    print(f"翻译结果 (法文): {translated_text_fr}")  # => Bonjour, le monde
