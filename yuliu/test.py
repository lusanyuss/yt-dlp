import logging
import time

import tensorflow as tf
import torch
from faster_whisper import WhisperModel

# 设置环境变量以避免 OpenMP 多重初始化的问题
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("TensorFlow 版本:", tf.__version__)
print("CUDA 可用 (TensorFlow):", tf.test.is_built_with_cuda())
print("GPU 可用 (TensorFlow):", tf.config.experimental.list_physical_devices('GPU'))

print("CUDA 可用 (PyTorch):", torch.cuda.is_available())
print("cuDNN 版本 (PyTorch):", torch.backends.cudnn.version())

if __name__ == '__main__':
    # 模型参数
    model_size = "large-v3"  # 模型大小
    device = "cuda"  # 使用 GPU
    compute_type = "float16"  # 计算类型
    audio_path = './res/out_times_00_audio_vocals.wav'

    # 加载模型
    logger.info("加载模型...")
    start_time = time.time()  # 记录模型加载开始时间
    model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
    end_time = time.time()  # 记录模型加载结束时间
    logger.info(f"模型加载时间: {end_time - start_time:.2f} 秒")

    # 开始转录
    logger.info("开始转录音频...")
    start_time = time.time()  # 记录转录开始时间
    # batched_model = BatchedInferencePipeline(model=model)
    # segments, info = batched_model.transcribe(audio_path, batch_size=4)

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language='zh',  # 如果已知语言，替换为实际语言代码
        condition_on_previous_text=False,
        vad_filter=True,  # 启用 VAD 过滤
        vad_parameters=dict(min_silence_duration_ms=200)  # 对话中可能有更短的停顿，设置为 200 毫秒
    )

    end_time = time.time()  # 记录转录结束时间
    logger.info(f"转录时间: {end_time - start_time:.2f} 秒\n\n")
    # 输出结果
    for segment in segments:
        logger.info("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    logger.info("\n\n结束。")
