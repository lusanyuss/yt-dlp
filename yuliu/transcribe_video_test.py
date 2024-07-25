from googletrans import Translator


def translate_text_with_model(target: str, text: str, model: str = "nmt") -> dict:
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, target_language=target, model=model)

    print("Text: {}".format(result["input"]))
    print("Translation: {}".format(result["translatedText"]))
    print("Detected source language: {}".format(result["detectedSourceLanguage"]))

    return result


def translate_text(target: str, text: str) -> dict:
    from google.cloud import translate_v2 as translate
    translate_client = translate.Client()
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate_client.translate(text, target_language=target)

    print("Text: {}".format(result["input"]))
    print("Translation: {}".format(result["translatedText"]))
    print("Detected source language: {}".format(result["detectedSourceLanguage"]))

    return result


def translate_text(text, dest='en'):
    translator = Translator()
    # 翻译文本到指定语言
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception as e:
        print(f"发生错误: {e}")
        return None


import asyncio
from google.cloud import translate_v3

async def translate_srt_file(input_uri, output_prefix):
    # Create a client
    client = translate_v3.TranslationServiceAsyncClient()

    # Initialize request argument(s)
    input_config = translate_v3.BatchDocumentInputConfig(
        gcs_source=translate_v3.GcsSource(input_uri=input_uri)
    )

    output_config = translate_v3.BatchDocumentOutputConfig(
        gcs_destination=translate_v3.GcsDestination(output_uri_prefix=output_prefix)
    )

    request = translate_v3.BatchTranslateDocumentRequest(
        parent="projects/radiant-works-430523-c8/locations/global",
        source_language_code="zh",
        target_language_codes=['en'],
        input_configs=[input_config],  # 这里要传递一个列表
        output_config=output_config,
    )

    # Make the request
    operation = await client.batch_translate_document(request=request)
    print("Waiting for operation to complete...")
    response = await operation.result()
    # Handle the response
    print(response)


if __name__ == "__main__":
    name = 'aa测试目录_cmn.srt'
    your_srt = f"gs://yuliu/{name}"  # 替换为你的SRT文件的GCS路径
    output_prefix = "gs://yuliu/output/"  # 替换为你的输出文件路径前缀
    asyncio.run(translate_srt_file(your_srt, output_prefix))

# if __name__ == '__main__':
#     your_srt = 'release_video/aa测试目录/aa测试目录_cmn.srt'
#     translate_srt_file(your_srt, 'aa测试目录')

# # 示例使用
# translated_text_en = translate_text('你好，世界', 'en')
# if translated_text_en:
#     print(f"翻译结果 (英文): {translated_text_en}")  # => Hello, world
#
# translated_text_jp = translate_text('你好，世界', 'ja')
# if translated_text_jp:
#     print(f"翻译结果 (日文): {translated_text_jp}")  # => こんにちは、世界
#
# translated_text_fr = translate_text('你好，世界', 'fr')
# if translated_text_fr:
#     print(f"翻译结果 (法文): {translated_text_fr}")  # => Bonjour, le monde
