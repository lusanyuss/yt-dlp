import warnings

from cryptography.utils import CryptographyDeprecationWarning

warnings.simplefilter("ignore", CryptographyDeprecationWarning)
import yuliu.utils
from yuliu import common, voice_utils

if __name__ == "__main__":
    # 单视频
    # run_command(['python', 'run.py', '--url', url])
    # url = "https://shls.mcloud.139.com/hls/KL04634eef94ee6f611ce5276a01f3f53a/playlist.m3u8?ci=1111aEx6R1E804320240509175614mlo"
    # run_command(['python', 'run.py','--sub_directory', sub_directory, '--download-only', '--url', url])
    # urls = [
    #     'https://shls.mcloud.139.com/hls/KP13b99d5ef390acb347d1046488c8b56e/playlist.m3u8?ci=1111aEx6R1E8042202407172027081nu&amp;fileSize=240841414&amp;usersiteid=usersite-s',
    # ]
    # download_only_videos(urls, "我的女儿是至尊")

    # check_and_run("武神太子归来", 3)
    # url = "https://shls.mcloud.139.com/hls/KL65a6914914be588034a5e8f6b02eed00/playlist.m3u8?ci=1111aEx6R1E807320240509175854swm"
    # run_command(['python', 'run.py', '--download-only', '--url', url])
    # 多视频
    # url = 'https://www.bilibili.com/video/BV1su411M78g/?spm_id_from=333.337.search-card.all.click&vd_source=34c946526337005bdabd03a6e52e4632'
    # run_command(['python', 'run.py', '--url', url])
    #
    # 本地视频(单)
    # video1 = os.path.join('download_cache', '1111864094_2675217.mp4')
    # run_command(['python', 'run.py', '--videos', video1])

    # 本地视频(多)
    # 定义视频文件夹和文件名模板
    # check_and_run('冰箱里的小人国', 5)
    # check_and_run('绝世神皇', 3)
    # check_and_run('玄门侠女', 84, 15, is_clear_cache=False)
    # check_and_run('丑女逆袭-被首富大佬缠上了', 1, 15, is_clear_cache=True)
    # check_and_run('玄门侠女', 1, 15, is_clear_cache=True)

    # check_and_run('我的老妈是女王', 1, 15, is_clear_cache=True)#有0家
    # check_and_run('隐秘的婚姻', 1, 15, is_clear_cache=True)#有0家
    #
    # check_and_run('九子夺嫡废太子竟是修仙者', 1, 15, is_clear_cache=True)#有3家
    # check_and_run('御龙刀主 举世欠我赊刀债', 1, 15, is_clear_cache=True)#有3家
    #
    # exit()

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
        '下山后我被四个绝色师姐包围了_test'

    ]

    mapping = yuliu.utils.get_title_index_mapping()

    for video_name in videos:
        cover_title_split_postion = 0
        index = mapping[video_name]
        sub_directory = f"{index}_{video_name}"

        if video_name == '隐龙之保安老爸不好惹':
            cover_title_split_postion = 3
        # if video_name == '重返地球我的圣人身份泄露了':
        #     cover_title_split_postion = 4
        # if video_name == '抓娃娃之女儿也要穷养':
        #     cover_title_split_postion = 3

        common.check_and_run(sub_directory=sub_directory,
                             video_name=video_name,
                             cover_title=video_name,
                             split_time_min=60,
                             crop_bottom=150,
                             crop_top=0,

                             is_test=True,
                             is_get_cover=True,
                             is_get_video=True,
                             is_get_fanyi=True,

                             num_of_covers=8,
                             cover_title_split_postion=cover_title_split_postion
                             )

    voice_utils.play_voice_message(f'程序执行完毕!!!')
