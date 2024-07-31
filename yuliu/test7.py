import torch
from transformers import BertTokenizer, BertForMaskedLM

# 加载预训练的BERT模型和分词器
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertForMaskedLM.from_pretrained('bert-base-chinese')
model.eval()


def correct_text(text):
    # 将文本分词并找到每个字符的位置
    tokenized_text = tokenizer.tokenize(text)
    input_ids = tokenizer.encode(text, return_tensors='pt')

    # 遍历每个字符位置，将其替换为[MASK]，然后预测该位置的字符
    corrected_text = list(text)
    for i, char in enumerate(tokenized_text):
        if char == '[UNK]':  # 跳过未识别的字符
            continue

        masked_input_ids = input_ids.clone()
        masked_input_ids[0][i + 1] = tokenizer.mask_token_id

        with torch.no_grad():
            outputs = model(masked_input_ids)
            predictions = outputs.logits

        predicted_index = torch.argmax(predictions[0, i + 1]).item()
        predicted_token = tokenizer.convert_ids_to_tokens([predicted_index])[0]

        if predicted_token != char:  # 如果预测的字符与原字符不同，则进行替换
            corrected_text[i] = predicted_token

    return ''.join(corrected_text)


if __name__ == '__main__':
    texts = [
        "他是个很好的耍子。",
        "今天天淅沥沥的下起了大鱼。",
        "我们要珍惜时间，好好学习，天天向下。",
        "她的笑容像阳光一洋灿烂。",
        "请你把铅笔见给我。"
    ]

    # 调用纠错函数
    for text in texts:
        corrected_text = correct_text(text)
        print(f"原文本: '{text}'")
        print(f"纠正后: '{corrected_text}'\n")
