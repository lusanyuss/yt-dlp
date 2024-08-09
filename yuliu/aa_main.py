import warnings

from cryptography.utils import CryptographyDeprecationWarning

from yuliu.VideoFrameProcessor import VideoFrameProcessor

warnings.simplefilter("ignore", CryptographyDeprecationWarning)
import yuliu.utils
from yuliu import common, voice_utils

if __name__ == "__main__":
    isTest = False
    # isTest = True
    videos = [
        ################### 已经部分 #######################
        ################### 未传部分 #######################
        # '为王问鼎,择日登基',
        # '了不起的妈妈',
        # '以我晚星映海川',
        # '傻了吧我有,一屋子美女房客',
        # '命中注定我爱你',
        # '工业之光',
        # '愤怒的父亲',
        # '我们都要活下去',
        # '我的傻父',
        # '浪子回头,浪子回头金不换',
        # '爱意随风起',
        # '闪婚对象竟是豪门大佬',
        # '闪婚老公竟想凭子上位',
        # '隐婚后,我的下属老公掉马甲了',
        # '青春不死常胜不衰'
        # '隐龙之保安老爸不好惹',



        # # 88-97
        # '光影下的少女',
        # '天王归来',



    ]

    mapping = yuliu.utils.get_title_index_mapping()

    for video_name in videos:
        cover_title_split_postion = 0
        index = mapping[video_name]
        sub_directory = f"{index}_{video_name}"

        if video_name == '我穿成了自己笔下反派男主':
            cover_title_split_postion = 4
        if video_name == '拜托都要死了谁还惯着你':
            cover_title_split_postion = 2
        if video_name == '退隐后三个美女住我家':
            cover_title_split_postion = 3
        if video_name == '丑女大翻身之换脸游戏':
            cover_title_split_postion = 2
        if video_name == '萌宝送上门爹地请签收':
            cover_title_split_postion = 2

        common.check_and_run(sub_directory=sub_directory,
                             video_name=video_name,
                             cover_title=video_name,
                             split_time_min=30,

                             # is_test=True,
                             is_get_cover=True,
                             # is_get_video=True,
                             is_get_fanyi=False,

                             num_of_covers=16,
                             cover_title_split_postion=cover_title_split_postion
                             )

    voice_utils.play_voice_message(f'程序执行完毕!!!')
