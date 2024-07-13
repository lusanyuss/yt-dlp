import os

from run_main import run_main


def check_and_run(sub_directory, cover_title, juji_num, split_time_min, is_clear_cache=False, number_covers=1, only_image=False):
    video_template = '{}.mp4'
    # 生成所有视频文件的路径
    videos = [os.path.join('download_cache', sub_directory, video_template.format(i)) for i in range(1, juji_num + 1)]
    # 检查文件是否存在
    missing_files = [video for video in videos if not os.path.exists(video)]
    if missing_files:
        print("以下视频文件缺失:")
        for missing_file in missing_files:
            print(missing_file)
    else:
        # 检查文件数是否与juji_num相等
        if len(videos) == juji_num:
            # 运行命令，添加base_directory和sub_directory参数
            print(f"所有 {juji_num} 个视频文件均存在，准备执行命令。")
            run_main(sub_directory=sub_directory,
                     cover_title=cover_title,
                     videos=videos,
                     split_time_min=split_time_min,
                     is_clear_cache=is_clear_cache,
                     number_covers=number_covers,
                     only_image=only_image)
        else:
            print(f"视频文件数量({len(videos)})与指定的剧集数量({juji_num})不相等，无法继续执行。")


def download_only_videos(urls, sub_directory):
    for index, url in enumerate(urls, start=1):
        run_main(sub_directory=sub_directory, video_name=str(index), download_only=True, url=url)


# 调用方法

if __name__ == "__main__":
    # 单视频
    # run_command(['python', 'run.py', '--url', url])
    # url = "https://shls.mcloud.139.com/hls/KL04634eef94ee6f611ce5276a01f3f53a/playlist.m3u8?ci=1111aEx6R1E804320240509175614mlo"
    # run_command(['python', 'run.py','--sub_directory', sub_directory, '--download-only', '--url', url])
    # urls = [
    #     # "https://shls.mcloud.139.com/hls/KL58ba7aa8bdd015ac572e35461f5a9886/playlist.m3u8?ci=1111aEx6R1E807420240711185644tin&fileSize=227692005&usersiteid=usersite-s",
    #     # "https://shls.mcloud.139.com/hls/KM129f246108a117d9b9d40c33a5407a4b/playlist.m3u8?ci=1111aEx6R1E807420240711185644tin",
    #     "https://shls.mcloud.139.com/hls/KLb4389cb4ea454acb02ff8c96466293c3/playlist.m3u8?ci=1111aEx6R1E80422024071118591106o&fileSize=54882704&usersiteid=usersite-s"
    # ]
    # download_only_videos(urls, "丑女逆袭-被首富大佬缠上了")

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

    videos = [
        # '丑女逆袭-被首富大佬缠上了',
        '我无敌于世间',
        '傅总您太太真的没死',
        '逃婚当天我抓了个总裁过日子',
        '萌宝助攻我帮妈妈改嫁总裁大佬',
        '分手渣男后她成了女首富',
        '为王问鼎,择日登基',
        # '九子夺嫡废太子竟是修仙者',
        '以我晚星映海川',
        '工业之光',
        # '御龙刀主$举世欠我赊刀债',
        '我的傻父',
        # '我的老妈是女王',
        '报告妈咪,爹地是总裁',
        '极品房东俏房客',
        '玄门侠女',
        # '隐秘的婚姻',
    ]
    for video_dir in videos:
        # check_and_run(video_dir, video_dir, 1, 15, is_clear_cache=True, number_covers=8, only_image=True)
        break

    check_and_run('aa测试目录', "萌宝助攻我帮妈妈改嫁总裁大佬", 1, 0.1, is_clear_cache=True, only_image=False)
