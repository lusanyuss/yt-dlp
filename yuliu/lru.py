from openlrc import LRCer
import os

# 解决 libiomp5md.dll 多次初始化的问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 初始化 LRCer
lrcer = LRCer()

# 生成字幕
# lrcer.run('./res/1.wav', target_lang='zh-cn')
lrcer.run('./res/1.wav', target_lang='zh-cn', bilingual_sub=True)
