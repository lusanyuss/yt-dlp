import warnings
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

# 检查 CUDA 设备是否可用
import torch
if not torch.cuda.is_available():
    print("没有可用的 CUDA 设备")



print(torch.cuda.is_available())
print(torch.cuda.device_count())
print(torch.cuda.get_device_name(0))

