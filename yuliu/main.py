# 调用方法

import yuliu.utils
from yuliu import common

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

        # '工业之光',
        # '傻了吧我有,一屋子美女房客',

        # '闪婚对象竟是豪门大佬',
        # '浪子回头,浪子回头金不换',
        # '以我晚星映海川',

        # '了不起的妈妈',
        # '命中注定我爱你',
        # '青春不死常胜不衰',
        # '我们都要活下去',
        # '新版-为母则刚',
        # '爱意随风起',
        # '愤怒的父亲',
        # '我的傻父',
        # '闪婚对象竟是豪门大佬',
        # '隐婚后,我的下属老公掉马甲了',

        '归来之非凡人生',
        '我竟然买断了首富的日常',
        '月光宝镜',
        '被交换的人生',
        '游子身上针',
        '隐龙之保安老爸不好惹',

    ]
    for video_name in videos:
        cover_title_split_postion = 0
        # if video_name == '我的爷爷是大佬':
        #     cover_title_split_postion = 2
        if video_name == '我竟然买断了首富的日常':
            cover_title_split_postion = 3

        common.check_and_run(sub_directory=video_name,
                             cover_title=yuliu.utils.replace_comma_with_newline(video_name),
                             juji_num=1,
                             split_time_min=15,
                             is_test=False,

                             is_get_cover=True,
                             is_get_video=True,
                             is_get_fanyi=True,
                             is_get_fanyi_other=False,

                             # is_get_video=False,
                             # is_get_fanyi=False,

                             num_of_covers=8,
                             is_high_quality=True,
                             cover_title_split_postion=cover_title_split_postion
                             )
