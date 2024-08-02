import pyttsx3

def play_voice_message(message):
    engine = pyttsx3.init()
    # 设置语速
    rate = engine.getProperty('rate')
    engine.setProperty('rate', 150)  # 语速可以根据需要调整
    # 设置音量
    volume = engine.getProperty('volume')
    engine.setProperty('volume', 1.0)  # 范围是0.0到1.0
    # 运行文本转语音
    engine.say(message)
    engine.runAndWait()

# 示例使用
if __name__ == "__main__":
    play_voice_message("你好，这是一个语音提示的示例。")
