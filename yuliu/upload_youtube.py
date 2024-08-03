import http.client as httplib  # updated import for http.client
import os
import random
import sys
import time

import httplib2
from googleapiclient.discovery import build  # updated import for googleapiclient
from googleapiclient.errors import HttpError  # updated import for googleapiclient
from googleapiclient.http import MediaFileUpload  # updated import for googleapiclient
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an googleapiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secret_lusanyuss.json"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.cloud.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}


def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        http = httplib2.Http(proxy_info=httplib2.ProxyInfo(
            proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
            proxy_host="127.0.0.1",
            proxy_port=7890
        ), timeout=60)
        args = argparser.parse_args(args=[])
        credentials = run_flow(flow, storage, args, http=http)
    else:
        http = httplib2.Http(proxy_info=httplib2.ProxyInfo(
            proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
            proxy_host="127.0.0.1",
            proxy_port=7890
        ), timeout=60)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(http))


def upload_video(file, title="Test Title", description="Test Description",
                 category="24", keywords="", privacy_status="private"):
    youtube = get_authenticated_service()
    tags = keywords.split(",") if keywords else None

    body = dict(
        snippet=dict(
            title=title,
            description=description,
            tags=tags,
            categoryId=category
        ),
        status=dict(
            privacyStatus=privacy_status
        )
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(file, chunksize=-1, resumable=True)
    )

    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("正在上传文件...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("视频 ID '%s' 上传成功。" % response['id'])
                else:
                    raise Exception("上传失败，响应内容: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "可重试的 HTTP 错误 %d 发生:\n%s" % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "可重试的错误发生: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception("重试次数过多，放弃上传。")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("休眠 %f 秒后重试..." % sleep_seconds)
            time.sleep(sleep_seconds)


# 使用示例
if __name__ == '__main__':
    videos = [
        '糟糕我被女神包围了',
        # '我站在巅峰从收到录取通知书开始',
        # '沉香如雪',
        # '死后第三年',
    ]
    for video_name in videos:
        title = video_name
        description = video_name
        upload_video(file=f"release_video/{video_name}/{video_name}_nobgm_final.mp4",
                     title=f"{title}",
                     description=f"{description}",
                     category="24",
                     keywords="",
                     privacy_status="private")
