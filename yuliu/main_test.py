# 调用方法
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
    common.check_and_run(sub_directory='aa测试目录',
                         cover_title="天龙八部",
                         juji_num=1,
                         split_time_min=0.5,

                         is_get_cover=True,
                         is_get_video=True,
                         is_get_fanyi=True,

                         num_of_covers=1,
                         is_high_quality=False,
                         cover_title_split_postion=0
                         )
