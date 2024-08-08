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

        # '请回答1990',
        # '重生之扭转乾坤',

        # # 88-97
        # '重生之我靠古玩再发家',
        # '儿臣请父皇退位',
        '气运将至',


        # '金手指1997',
        # '龙归故里',
        # '神医驸马爷',
        # '至尊国士',
        # '裁员裁到大动脉第二部',



        # '一场误会的闪婚契约',

    ]

    mapping = yuliu.utils.get_title_index_mapping()

    for video_name in videos:
        cover_title_split_postion = 0
        index = mapping[video_name]
        sub_directory = f"{index}_{video_name}"

        if video_name == '重返流金岁月回档2011当歌神':
            cover_title_split_postion = 6
        if video_name == '真假千金姐姐死后成为霸总白月光':
            cover_title_split_postion = 6
        if video_name == '重生之我靠古玩再发家':
            cover_title_split_postion = 3

        common.check_and_run(sub_directory=sub_directory,
                             video_name=video_name,
                             cover_title=video_name,
                             split_time_min=30,

                             # is_test=True,
                             is_get_cover=True,
                             is_get_video=True,
                             is_get_fanyi=False,

                             num_of_covers=8,
                             cover_title_split_postion=cover_title_split_postion
                             )

    voice_utils.play_voice_message(f'程序执行完毕!!!')
