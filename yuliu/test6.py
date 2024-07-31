import torch
from transformers import BertTokenizer, BertForMaskedLM

# 加载分词器和模型
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertForMaskedLM.from_pretrained('bert-base-chinese')
model.eval()  # 设置为评估模式

def compare_texts(texts1, texts2):
    assert len(texts1) == len(texts2), "两个列表必须长度相同"

    # 函数：批量计算文本的平均对数似然度
    def score_texts(texts):
        tokenize_input = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        input_ids = tokenize_input["input_ids"]
        with torch.no_grad():
            outputs = model(input_ids, labels=input_ids)
        # 这里应该直接返回标量值，而不是数组
        return outputs.loss.item()  # 从这里返回标量值

    # 为两组文本计算得分
    scores1 = [score_texts([text]) for text in texts1]  # 使用列表生成式来处理每个文本
    scores2 = [score_texts([text]) for text in texts2]

    # 比较每对文本的得分，选择得分较低（更自然）的文本
    better_texts = [texts1[i] if scores1[i] < scores2[i] else texts2[i] for i in range(len(texts1))]
    return better_texts

if __name__ == '__main__':

    # 示例使用
    texts1 = ["你去外面守看吧"] * 1000  # 示例文本列表1
    texts2 = ["你去外面守着吧"] * 1000  # 示例文本列表2

    # 调用函数
    better_texts = compare_texts(texts1, texts2)

    # 输出结果
    for text in better_texts[:10]:  # 只展示前10个结果
        print(f"更自然的文本是: '{text}'")
