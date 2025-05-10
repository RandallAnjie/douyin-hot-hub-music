import contextlib
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

HOT_SEARCH_URL = 'https://aweme.snssdk.com/aweme/v1/hot/search/list/'
HOT_STAR_URL = 'https://aweme.snssdk.com/aweme/v1/hotsearch/star/billboard/'
HOT_LIVE_URL = 'https://webcast.amemv.com/webcast/ranklist/hot/'
BRAND_CATEGORY_URL = 'https://aweme.snssdk.com/aweme/v1/hotsearch/brand/category/'
HOT_BRAND_URL = 'https://aweme.snssdk.com/aweme/v1/hotsearch/brand/billboard/'
HOT_MUSIC_URL = 'https://aweme.snssdk.com/aweme/v1/chart/music/list/'

HEADERS = {
    'user-agent': 'okhttp3'
}
QUERIES = {
    'device_platform': 'android',
    'version_name': '13.2.0',
    'version_code': '130200',
    'aid': '1128'
}
RETRIES = Retry(total=3,
                backoff_factor=1,
                status_forcelist=[k for k in range(400, 600)])


@contextlib.contextmanager
def request_session():
    s = requests.session()
    try:
        s.headers.update(HEADERS)
        s.mount("http://", HTTPAdapter(max_retries=RETRIES))
        s.mount("https://", HTTPAdapter(max_retries=RETRIES))
        yield s
    finally:
        s.close()


class Douyin:
    def get_hot_music(self):
        """
            {
                "music_info": {
                    "album": "四季予你",
                    "cover_thumb": {
                    "width": 720,
                    "height": 720,
                    "uri": "iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg",
                    "url_list": [
                        "https://p9-dy.byteimg.com/aweme/100x100/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p6-dy-ipv6.byteimg.com/aweme/100x100/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg"
                    ]
                    },
                    "source_platform": 10036,
                    "is_restricted": false,
                    "is_video_self_see": false,
                    "play_url": {
                    "uri": "https://sf3-dycdn-tos.pstatp.com/obj/iesmusic-cn-local/v1/tt-obj/2241bef2d16820c170109557dbfd940c.mp3",
                    "url_list": [
                        "https://sf3-dycdn-tos.pstatp.com/obj/iesmusic-cn-local/v1/tt-obj/2241bef2d16820c170109557dbfd940c.mp3",
                        "https://sf6-dycdn-tos.pstatp.com/obj/iesmusic-cn-local/v1/tt-obj/2241bef2d16820c170109557dbfd940c.mp3"
                    ],
                    "width": 720,
                    "height": 720,
                    "url_key": "6907550512367864584"
                    },
                    "preview_start_time": 67.4,
                    "cover_large": {
                    "uri": "iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg",
                    "url_list": [
                        "https://p9-dy.byteimg.com/aweme/720x720/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p6-dy-ipv6.byteimg.com/aweme/720x720/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "prevent_download": false,
                    "unshelve_countries": null,
                    "preview_end_time": 0,
                    "shoot_duration": 18,
                    "lyric_short_position": null,
                    "mute_share": false,
                    "tag_list": null,
                    "is_matched_metadata": false,
                    "is_audio_url_with_cookie": false,
                    "author": "程响",
                    "id_str": "6907550512367864584",
                    "collect_stat": 0,
                    "offline_desc": "",
                    "avatar_thumb": {
                    "uri": "2f8d90002d445edafadbe",
                    "url_list": [
                        "https://p9-dy.byteimg.com/aweme/100x100/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p6-dy-ipv6.byteimg.com/aweme/100x100/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p3-dy-ipv6.byteimg.com/aweme/100x100/2f8d90002d445edafadbe.jpeg?from=4010531038"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "matched_song": {
                    "title": "四季予你（剪辑版）",
                    "h5_url": "https://sf6-scmcdn-tos.pstatp.com/goofy/toutiao/canon/douyin/canon/index.html",
                    "cover_medium": {
                        "uri": "iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg",
                        "url_list": [
                        "https://p9.douyinpic.com/aweme/200x200/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p6-dy-ipv6.byteimg.com/aweme/200x200/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p3-dy-ipv6.byteimg.com/aweme/200x200/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg"
                        ],
                        "width": 720,
                        "height": 720
                    },
                    "id": "6909031453405923330",
                    "author": "程响"
                    },
                    "can_background_play": true,
                    "cover_medium": {
                    "uri": "iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg",
                    "url_list": [
                        "https://p9-dy.byteimg.com/aweme/200x200/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p6-dy-ipv6.byteimg.com/aweme/200x200/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "binded_challenge_id": 0,
                    "music_chart_ranks": null,
                    "strong_beat_url": {
                    "uri": "https://sf-tk-sg.ibytedtos.com/obj/tiktok-obj/strong_beat/1687613061406721",
                    "url_list": [
                        "https://sf-tk-sg.ibytedtos.com/obj/tiktok-obj/strong_beat/1687613061406721"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "is_commerce_music": false,
                    "id": 6907550512367864584,
                    "dmv_auto_show": false,
                    "author_position": null,
                    "duration": 18,
                    "prevent_item_download_status": 0,
                    "extra": "{\"beats\":{},\"hotsoon_review_time\":-1,\"aggregate_exempt_conf\":[],\"has_edited\":0,\"review_unshelve_reason\":0,\"douyin_beats_info\":{},\"schedule_search_time\":0,\"music_label_id\":1257,\"reviewed\":1}",
                    "user_count": 662543,
                    "owner_handle": "",
                    "is_original": false,
                    "is_del_video": false,
                    "external_song_info": [],
                    "avatar_large": {
                    "uri": "2f8d90002d445edafadbe",
                    "url_list": [
                        "https://p26-dy.byteimg.com/aweme/1080x1080/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p3-dy-ipv6.byteimg.com/aweme/1080x1080/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p29-dy.byteimg.com/aweme/1080x1080/2f8d90002d445edafadbe.jpeg?from=4010531038"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "audition_duration": 18,
                    "position": null,
                    "reason_type": 0,
                    "title": "四季予你（剪辑版）",
                    "author_deleted": false,
                    "artists": [],
                    "cover_hd": {
                    "uri": "iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg",
                    "url_list": [
                        "https://p9-dy.byteimg.com/aweme/1080x1080/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg",
                        "https://p6-dy-ipv6.byteimg.com/aweme/1080x1080/iesmusic-cn-local/v1/tt-obj/image/c3297eb70e9c1abf01e07151fbeee2cd.jpg.jpeg"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "status": 1,
                    "owner_nickname": "",
                    "mid": "6907550512367864584",
                    "avatar_medium": {
                    "uri": "2f8d90002d445edafadbe",
                    "url_list": [
                        "https://p6-dy-ipv6.byteimg.com/aweme/720x720/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p1.douyinpic.com/aweme/720x720/2f8d90002d445edafadbe.jpeg?from=4010531038",
                        "https://p29-dy.byteimg.com/aweme/720x720/2f8d90002d445edafadbe.jpeg?from=4010531038"
                    ],
                    "width": 720,
                    "height": 720
                    },
                    "is_original_sound": false
                },
                "heat": 17611210,
                "can_background_play": true,
                "has_copyright": true
            }
        """
        items = []
        resp = None
        try:
            with request_session() as s:
                params = QUERIES.copy()
                params.update(
                    {'chart_id': '6853972723954146568', 'count': '100'})
                resp = s.get(HOT_MUSIC_URL, params=params)
                obj = json.loads(resp.text)
                music_list = obj['music_list']
                items = [item for item in music_list]
        except:
            logger.exception('get hot music failed')
        return (items, resp)


if __name__ == "__main__":
    dy = Douyin()

    items, text = dy.get_hot_brand(category=10)
    for item in items:
        logger.info('item:%s', item)

