# 调用方法
from yuliu import common, voice_utils
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.simplefilter("ignore", CryptographyDeprecationWarning)

if __name__ == "__main__":

    sub_directory = 'aa测试目录'
    common.check_and_run(sub_directory=sub_directory,
                         cover_title=sub_directory,

                         split_time_min=240,
                         is_test=True,

                         is_get_cover=True,
                         is_get_video=True,
                         is_get_fanyi=True,

                         num_of_covers=1,
                         cover_title_split_postion=0
                         )
    voice_utils.play_voice_message(f'测试程序执行完毕!!!')
