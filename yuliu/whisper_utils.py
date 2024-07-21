# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Tiny
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Base
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Small
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Medium
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Large
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Tiny.en
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Base.en
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Small.en
# whisper ./yuliu/res/out_times_00_audio_vocals.wav --model Medium.en
#
#
# whisperx ./yuliu/res/zh1.wav
# whisperx --model large-v2 --language de examples/sample_de_01.wav
# whisperx --model large-v2 --language zh ./yuliu/res/zh1.wav
whisperx --model large-v2 --language zh --compute_type float32 ./yuliu/res/zh1.wav
whisperx --model large-v2 --language zh --compute_type float32 ./yuliu/res/zh1.wav --output_dir ./yuliu/res/ --output_format srt
whisperx --model large-v2 --language zh --compute_type float32 ./yuliu/res/zh1.wav --output_dir ./yuliu/res/ --output_format srt --highlight_words True

openlrc transcribe --model large-v2 --language zh ./yuliu/res/zh1.wav -o ./yuliu/res/zh1.lrc
openlrc transcribe --model large-v2 --language zh ./yuliu/res/zh1.wav -o ./yuliu/res/zh1.lrc




