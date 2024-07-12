import paddle
import paddle.fluid as fluid

# 检查PaddlePaddle是否使用GPU
print("Is PaddlePaddle using GPU:", paddle.is_compiled_with_cuda())

# 获取GPU数量
print("Number of GPUs available:", fluid.core.get_cuda_device_count())

# 检查CUDA版本和cuDNN版本
cuda_version = fluid.core.get_cuda_version()
cudnn_version = fluid.core.get_cudnn_version()
print("CUDA version:", cuda_version)
print("cuDNN version:", cudnn_version)
