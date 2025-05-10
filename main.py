import os
import time
import urllib
import json
import requests
import asyncio
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

from requests import Response

import util
from douyin import Douyin
from util import logger

# 添加请求头
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def generate_archive_md(musics):
    """生成今日readme
    """

    def music(item):
        info = item['music_info']
        title = info['title']
        author = info['author']
        if 'play_url' in info:
            play_url = info['play_url']['uri']
            return '1. [{}]({}) - {}'.format(title, play_url, author)
        return '1. {} - {}'.format(title, author)


    musicMd = '暂无数据'
    if musics:
        musicMd = '\n'.join([music(item) for item in musics])

    readme = ''
    file = os.path.join('template', 'archive.md')
    with open(file) as f:
        readme = f.read()

    now = util.current_time()
    readme = readme.replace("{updateTime}", now)
    readme = readme.replace("{musics}", musicMd)

    return readme


def generate_readme(musics):
    """生成今日readme
    """
    def search(item):
        word = item['word']
        url = 'https://www.douyin.com/search/' + urllib.parse.quote(word)
        return '1. [{}]({})'.format(word, url)

    def star(item):
        name = item['user_info']['nickname']
        uid = item['user_info']['uid']
        suid = item['user_info']['sec_uid']
        url = 'https://www.iesdouyin.com/share/user/{}?sec_uid={}'.format(
            uid, suid)
        return '1. [{}]({})'.format(name, url)

    def live(item):
        uid = item['user']['id']
        suid = item['user']['sec_uid']
        nickname = item['user']['nickname']
        title = item['room']['title']
        roomid = item['room']['id']
        user_url = 'https://www.iesdouyin.com/share/user/{}?sec_uid={}'.format(
            uid, suid)
        live_url = 'https://webcast.amemv.com/webcast/reflow/'+str(roomid)
        if not title:
            title = '看直播'
        return '1. [{}]({}) - [{}]({})'.format(title, live_url, nickname, user_url)

    def music(item):
        info = item['music_info']
        title = info['title']
        author = info['author']
        if 'play_url' in info:
            play_url = info['play_url']['uri']
            return '1. [{}]({}) - {}'.format(title, play_url, author)
        return '1. {} - {}'.format(title, author)

    musicMd = '暂无数据'
    if musics:
        musicMd = '\n'.join([music(item) for item in musics])

    readme = ''
    file = os.path.join('template', 'README.md')
    with open(file) as f:
        readme = f.read()

    now = util.current_time()
    readme = readme.replace("{updateTime}", now)

    readme = readme.replace("{musics}", musicMd)

    return readme


def save_readme(md):
    logger.info('today md:%s', md)
    util.write_text('README.md', md)


def save_archive_md(md):
    logger.info('archive md:%s', md)
    name = util.current_date()+'.md'
    file = os.path.join('archives', name)
    util.write_text(file, md)


def save_raw_response(resp: Response, filename: str):
    """保存原始响应内容
    """
    if resp:
        content = resp.text
        filename = '{}.json'.format(filename)
        logger.info('save response:%s', filename)
        date = util.current_date()
        file = os.path.join('raw', date, filename)
        util.write_text(file, content)
        file = os.path.join(filename)
        util.write_text(file, content)


def save_brand_raw_response(resp: Response, category: str):
    """保存品牌榜响应内容
    """
    if resp:
        content = resp.text
        date = util.current_date()
        filename = '{}.json'.format(category)
        logger.info('save response:%s', filename)
        file = os.path.join('raw', date, 'brand', filename)
        util.write_text(file, content)


def generate_brand_table_md(brand_map: map):
    """品牌榜md
    """
    fake_brand = {'name': '-'}

    def column(item):
        if item is fake_brand:
            return fake_brand['name']

        name = item['name']
        key = urllib.parse.quote(name)
        search_url = 'https://www.baidu.com/s?wd={}'.format(key)
        return '[{}]({})'.format(name, search_url)

    def ensure_same_len(brand_map: map):
        max_len = 0
        for category in brand_map:
            max_len = max(max_len, len(brand_map[category]))
        for category in brand_map:
            brands: list = brand_map[category]
            if len(brands) < max_len:
                brands.extend([fake_brand for _ in range(max_len-len(brands))])
        return max_len

    # 确保品牌列表长度相同
    max_len = ensure_same_len(brand_map)

    # 表头
    table_header = '|'
    for category in brand_map:
        table_header += ' {} |'.format(category)
    table_header += '\n'
    table_header += '|'
    for _ in range(len(brand_map)):
        table_header += ' --- |'
    # 表行
    table_rows = ''
    for i in range(max_len):
        row = '|'
        for category in brand_map:
            brands: list = brand_map[category]
            row += ' {} |'.format(column(brands[i]))
        table_rows += row + '\n'

    return table_header + '\n' + table_rows


def get_all_brands(dy: Douyin):
    """热门品牌
    """
    categories, resp = dy.get_brand_category()
    save_raw_response(resp, 'brand-category')
    time.sleep(1)

    brand_map = {}
    for category in categories:
        # 分类名称
        cname = category['name']
        cid = int(category['id'])
        brands, resp = dy.get_hot_brand(cid)
        save_brand_raw_response(resp, cname)
        brand_map[cname] = brands
        time.sleep(1)

    return brand_map


async def fetch_and_format_lyrics(lyric_url):
    """获取并格式化歌词
    
    Args:
        lyric_url: 歌词URL
        
    Returns:
        tuple: (格式化的歌词文本, 歌词数据列表)
    """
    try:
        formatted_lyrics = ""
        lyrics_data = []
        
        if not lyric_url:
            return formatted_lyrics, lyrics_data
            
        response = requests.get(lyric_url, headers=HEADERS)
        response.raise_for_status()
        
        # 尝试解析JSON内容
        try:
            lyrics_json = response.json()
        except:
            # 如果不是JSON格式，可能是纯文本LRC或其他格式
            formatted_lyrics = response.text
            return formatted_lyrics, lyrics_data
        
        # 检查是否为空
        if not lyrics_json:
            return formatted_lyrics, lyrics_data
            
        # 处理歌词数据 - 两种可能的格式
        if isinstance(lyrics_json, list):
            # 处理直接返回数组的格式 [{"text":"歌词","timeId":"秒数"}]
            logger.info(f"检测到数组格式的歌词，共 {len(lyrics_json)} 行")
            
            for line in lyrics_json:
                if "text" in line and "timeId" in line:
                    time_seconds = float(line["timeId"])
                    minutes = int(time_seconds // 60)
                    seconds = time_seconds % 60
                    milliseconds = int((seconds - int(seconds)) * 1000)
                    
                    time_stamp = f"[{minutes:02d}:{int(seconds):02d}.{milliseconds:03d}]"
                    formatted_line = f"{time_stamp} {line['text']}"
                    formatted_lyrics += formatted_line + "\n"
                    
                    lyrics_data.append({
                        "start_time": time_seconds,
                        "end_time": time_seconds + 5,  # 估计结束时间，可能不准确
                        "content": line["text"]
                    })
                    
        elif "lines" in lyrics_json:
            # 处理有lines字段的标准格式
            logger.info("检测到标准格式的歌词对象")
            lines = lyrics_json.get("lines", [])
            for line in lines:
                start_time = line.get("start_time", 0) / 1000.0  # 转换为秒
                end_time = line.get("end_time", 0) / 1000.0  # 转换为秒
                content = line.get("content", "")
                
                if content:
                    time_stamp = f"[{int(start_time/60):02d}:{int(start_time%60):02d}.{int((start_time*1000)%1000):03d}]"
                    formatted_line = f"{time_stamp} {content}"
                    formatted_lyrics += formatted_line + "\n"
                    
                    lyrics_data.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "content": content
                    })
            
        # 如果依然没有解析出内容，可能是其他格式，直接保存原始内容
        if not formatted_lyrics and lyrics_json:
            formatted_lyrics = str(lyrics_json)
            logger.warning("无法解析歌词格式，保存原始内容")
            
        logger.info(f"成功格式化歌词，共 {len(lyrics_data)} 行")
        return formatted_lyrics, lyrics_data
    except Exception as e:
        logger.error(f"获取歌词失败: {str(e)}")
        logger.exception("歌词获取详细错误")
        return "", []

async def extract_chorus_lyrics(lyrics_data, start_time, duration):
    """提取高潮部分歌词
    
    Args:
        lyrics_data: 歌词数据列表
        start_time: 高潮开始时间(秒)
        duration: 高潮持续时间(秒)
        
    Returns:
        str: 高潮部分歌词
    """
    try:
        if not lyrics_data:
            return ""
            
        end_time = start_time + duration
        chorus_lyrics = ""
        
        for line in lyrics_data:
            line_start = line.get("start_time", 0)
            line_end = line.get("end_time", 0)
            
            # 如果行的开始或结束时间在高潮段内，或者高潮段完全包含这一行
            if (line_start >= start_time and line_start < end_time) or \
               (line_end > start_time and line_end <= end_time) or \
               (line_start <= start_time and line_end >= end_time):
                content = line.get("content", "")
                if content:
                    time_stamp = f"[{int(line_start/60):02d}:{int(line_start%60):02d}.{int((line_start*1000)%1000):03d}]"
                    chorus_lyrics += f"{time_stamp} {content}\n"
                    
        return chorus_lyrics
    except Exception as e:
        logger.error(f"提取高潮歌词失败: {str(e)}")
        return ""

async def analyze_and_save_music(music_item, rank=0):
    """分析音乐数据并保存到JSON和文件
    
    Args:
        music_item: 音乐数据
        rank: 音乐排名
    """
    try:
        # 创建assets目录结构
        assets_dir = os.path.join("assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        # 创建子目录
        music_dir = os.path.join(assets_dir, "music")
        chorus_dir = os.path.join(assets_dir, "chorus")
        lyrics_dir = os.path.join(assets_dir, "lyrics")
        chorus_lyrics_dir = os.path.join(assets_dir, "chorus_lyrics")
        
        for directory in [music_dir, chorus_dir, lyrics_dir, chorus_lyrics_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 获取当前时间
        current_time = time.time()
        current_datetime = time.strftime("%Y-%m-%d %H:%M", time.localtime(current_time))
        
        # 提取音乐信息
        music_info = music_item.get("music_info", {})
        heat = music_item.get("heat", 0)
        has_copyright = music_item.get("has_copyright", False)
        can_background_play = music_item.get("can_background_play", False)
        
        music_id = music_info.get("id_str", "")
        title = music_info.get("title", "")
        author = music_info.get("author", "")
        album = music_info.get("album", "")
        user_count = music_info.get("user_count", 0)
        duration = music_info.get("duration", 0)
        
        # 格式化时长
        duration_formatted = f"{duration:.0f}秒" if duration else "0秒"
        
        # 初始化变量，避免未定义错误
        chorus_start_seconds = None
        chorus_duration_seconds = None
        chorus_path = ""
        chorus_lyrics_path = ""
        raw_lyrics_path = ""
        cover_image_path = ""
        high_peak_time_range = ""
        
        # 判断是否为汽水音乐
        is_aed_music_flag = False
        
        # 从extra字段中提取汽水音乐信息和标签
        music_tags = {}
        if "extra" in music_info:
            extra = music_info.get("extra")
            # 如果extra是字符串，尝试解析为JSON
            if isinstance(extra, str):
                try:
                    extra_dict = json.loads(extra)
                    # 检查汽水音乐标志
                    if extra_dict.get("is_aed_music") == 1 or extra_dict.get("with_aed_model") == 1:
                        is_aed_music_flag = True
                        
                    # 提取音乐标签
                    music_tagging = extra_dict.get("music_tagging", {})
                    music_tags = {
                        "Languages": music_tagging.get("Languages", []),
                        "Moods": music_tagging.get("Moods", []),
                        "Genres": music_tagging.get("Genres", []),
                        "Themes": music_tagging.get("Themes", []),
                        "SingingVersions": music_tagging.get("SingingVersions", [])
                    }
                except:
                    logger.error(f"解析音乐extra字段失败: {extra}")
            elif isinstance(extra, dict):
                # 如果已经是字典，直接获取
                if extra.get("is_aed_music") == 1 or extra.get("with_aed_model") == 1:
                    is_aed_music_flag = True
                    
                # 提取音乐标签
                music_tagging = extra.get("music_tagging", {})
                music_tags = {
                    "Languages": music_tagging.get("Languages", []),
                    "Moods": music_tagging.get("Moods", []),
                    "Genres": music_tagging.get("Genres", []),
                    "Themes": music_tagging.get("Themes", []),
                    "SingingVersions": music_tagging.get("SingingVersions", [])
                }
        
        # 下载并保存封面图片
        if music_info.get("cover_hd"):
            try:
                cover_url = music_info.get("cover_hd", {}).get("url_list", [""])[0]
                if cover_url:
                    # 创建目录存放图片
                    images_dir = os.path.join(assets_dir, "images")
                    os.makedirs(images_dir, exist_ok=True)
                    cover_image_path = os.path.join(images_dir, f"{music_id}.jpg")
                    
                    # 下载图片
                    logger.info(f"尝试下载封面图: {cover_url}")
                    response = requests.get(cover_url, headers=HEADERS, stream=True)
                    response.raise_for_status()
                    
                    # 保存图片
                    with open(cover_image_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    cover_image_path = os.path.relpath(cover_image_path, assets_dir)
            except Exception as e:
                logger.error(f"处理封面图失败: {str(e)}")
        
        # 下载并保存音频文件
        audio_path = ""
        is_full_audio = False
        if music_info.get("play_url"):
            try:
                audio_url = music_info.get("play_url", {}).get("url_list", [""])[0]
                if audio_url:
                    audio_path = os.path.join(music_dir, f"{music_id}.mp3")
                    
                    # 下载音频
                    logger.info(f"尝试下载音频: {audio_url}")
                    response = requests.get(audio_url, headers=HEADERS, stream=True)
                    response.raise_for_status()
                    
                    # 保存音频
                    with open(audio_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # 检查音频时长 - 使用ffmpeg替代mutagen
                    try:
                        # 使用ffmpeg获取音频时长
                        cmd = [
                            'ffmpeg', '-i', audio_path, 
                            '2>&1'  # 重定向错误输出到标准输出
                        ]
                        try:
                            # 使用ffprobe更适合获取媒体信息
                            import subprocess
                            ffprobe_cmd = [
                                'ffprobe', '-v', 'error', '-show_entries', 
                                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                                audio_path
                            ]
                            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
                            if result.returncode == 0 and result.stdout.strip():
                                actual_duration = float(result.stdout.strip())
                                logger.info(f"音频实际时长(ffprobe): {actual_duration:.2f}秒")
                                
                                # 检查高潮部分信息
                                if chorus_start_seconds is not None and chorus_duration_seconds is not None:
                                    # 计算高潮片段时长
                                    chorus_length = chorus_duration_seconds
                                    # 如果实际音频时长与高潮片段时长接近（允许5秒差异）
                                    if abs(actual_duration - chorus_length) < 5.0:
                                        logger.warning(f"检测到音频时长({actual_duration:.2f}秒)与高潮片段时长({chorus_length:.2f}秒)接近，可能是高潮片段而非完整音频")
                                        is_full_audio = False
                                    # 如果实际音频时长明显短于API提供的音频时长（允许3秒差异）
                                    elif duration > 0 and actual_duration < duration - 3.0:
                                        logger.warning(f"检测到音频时长({actual_duration:.2f}秒)明显短于API提供的时长({duration:.2f}秒)，可能不是完整音频")
                                        is_full_audio = False
                        except (subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
                            logger.error(f"使用ffprobe获取音频时长失败: {str(e)}")
                            logger.warning("尝试使用API提供的时长信息")
                    except Exception as e:
                        logger.error(f"检测音频时长失败: {str(e)}")
                        logger.exception("音频时长检测详细错误")
                    
                    audio_path = os.path.relpath(audio_path, assets_dir)
            except Exception as e:
                logger.error(f"处理音频失败: {str(e)}")
                logger.exception("音频处理详细错误")

        # 处理高潮部分
        chorus_start_ms = None
        chorus_duration_ms = None
        
        # 默认假设音频是高潮片段，除非能成功截取出高潮部分
        is_full_audio = False
        chorus_path = None
        
        # 获取歌曲信息中的高潮部分数据
        song_info = music_info.get("song", {})
        if song_info and "chorus" in song_info:
            try:
                chorus = song_info.get("chorus", {})
                chorus_start_ms = chorus.get("start_ms")
                chorus_duration_ms = chorus.get("duration_ms")
                
                if chorus_start_ms is not None and chorus_duration_ms is not None:
                    # 将毫秒转换为秒，并保留小数精度
                    chorus_start_seconds = float(chorus_start_ms) / 1000.0
                    chorus_duration_seconds = float(chorus_duration_ms) / 1000.0
                    
                    # 检查高潮时间是否合理（不应超过音乐总时长）
                    if (chorus_start_seconds + chorus_duration_seconds) > (duration * 1.1):  # 允许10%的误差
                        logger.warning(f"高潮时间段可能超出音乐总时长，尝试调整单位")
                        # 如果时间明显不合理，检查是否单位问题（某些API可能直接返回秒而非毫秒）
                        if chorus_start_ms < 1000 and chorus_duration_ms < 1000:
                            # 如果值小于1000，很可能已经是秒而非毫秒
                            chorus_start_seconds = float(chorus_start_ms)
                            chorus_duration_seconds = float(chorus_duration_ms)
                            logger.info(f"已调整高潮时间单位: 开始={chorus_start_seconds}秒, 持续={chorus_duration_seconds}秒")
                    
                    # 验证高潮段是否在音频范围内
                    is_chorus_valid = chorus_start_seconds < duration and (chorus_start_seconds + chorus_duration_seconds) <= (duration * 1.1)
                    
                    # 如果高潮段有效且有音频文件，处理高潮音频
                    if is_chorus_valid and audio_path:
                        # 确保音频文件存在
                        full_audio_path = os.path.join(assets_dir, audio_path)
                        if os.path.exists(full_audio_path):
                            chorus_path = os.path.join(chorus_dir, f"{music_id}_chorus.mp3")
                            
                            # 使用ffmpeg截取高潮部分
                            try:
                                logger.info(f"正在截取高潮部分: 开始时间={chorus_start_seconds}秒, 持续时间={chorus_duration_seconds}秒")
                                
                                cmd = [
                                    'ffmpeg', '-i', full_audio_path, 
                                    '-ss', str(chorus_start_seconds), 
                                    '-t', str(chorus_duration_seconds),
                                    '-q:a', '0', 
                                    '-y',  # 覆盖已存在的文件
                                    chorus_path
                                ]
                                subprocess.run(cmd, check=True)
                                chorus_path = os.path.relpath(chorus_path, assets_dir)
                                logger.info(f"成功截取高潮音频: {chorus_path}")
                                
                                # 只有成功截取了高潮片段，才认为原始音频是完整版
                                is_full_audio = True
                                logger.info("成功截取高潮部分，确认原始音频为完整版")
                            except Exception as e:
                                logger.error(f"截取高潮音频失败: {str(e)}")
                                # 截取失败，也认为原始音频是高潮片段
                                is_full_audio = False
                                logger.info("截取高潮部分失败，判断原始音频可能为高潮片段")
                    elif not is_chorus_valid:
                        logger.warning(f"高潮段时间超出音频时长，跳过高潮段截取: 开始={chorus_start_seconds}秒, 持续={chorus_duration_seconds}秒, 音频总长={duration}秒")
                        logger.info("无法截取高潮部分，判断原始音频为高潮片段")
                        
                        # 检查原始音频是否可能已经是高潮片段
                        try:
                            full_audio_path = os.path.join(assets_dir, audio_path)
                            if os.path.exists(full_audio_path):
                                # 获取音频实际时长
                                ffprobe_cmd = [
                                    'ffprobe', '-v', 'error', '-show_entries', 
                                    'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                                    full_audio_path
                                ]
                                result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
                                if result.returncode == 0 and result.stdout.strip():
                                    actual_duration = float(result.stdout.strip())
                                    
                                    # 如果原始音频时长与高潮片段时长接近（允许5秒差异）
                                    if abs(actual_duration - chorus_duration_seconds) < 5.0:
                                        logger.info(f"检测到原始音频时长({actual_duration:.2f}秒)与高潮片段时长({chorus_duration_seconds:.2f}秒)接近，判断原始音频已经是高潮片段")
                                        
                                        # 复制一份音频文件作为高潮片段
                                        chorus_path = os.path.join(chorus_dir, f"{music_id}_chorus.mp3")
                                        shutil.copy(full_audio_path, chorus_path)
                                        chorus_path = os.path.relpath(chorus_path, assets_dir)
                                        logger.info(f"已将原始音频复制为高潮片段: {chorus_path}")
                                    # 添加新的判断逻辑：如果原始音频明显短于完整音频时长，且有高潮段信息，也视为高潮片段
                                    elif duration > 0 and actual_duration < duration * 0.75 and chorus_duration_seconds > 0:
                                        logger.info(f"检测到原始音频时长({actual_duration:.2f}秒)明显短于API提供的总时长({duration:.2f}秒)，且存在高潮信息，判断原始音频是高潮片段")
                                        
                                        # 复制一份音频文件作为高潮片段
                                        chorus_path = os.path.join(chorus_dir, f"{music_id}_chorus.mp3")
                                        shutil.copy(full_audio_path, chorus_path)
                                        chorus_path = os.path.relpath(chorus_path, assets_dir)
                                        logger.info(f"已将原始音频复制为高潮片段: {chorus_path}")
                        except Exception as e:
                            logger.error(f"检查原始音频是否为高潮片段失败: {str(e)}")
            except Exception as e:
                logger.error(f"处理高潮部分失败: {str(e)}")
        else:
            logger.info("无高潮部分信息，无法确定音频类型，默认认为是完整版")
            is_full_audio = True
        
        # 处理歌词
        lyrics_path = ""
        formatted_lyrics = ""
        lyrics_data = []
        
        if music_info.get("lyric_url"):
            try:
                lyric_url = music_info.get("lyric_url")
                logger.info(f"正在获取歌词: {lyric_url}")
                formatted_lyrics, lyrics_data = await fetch_and_format_lyrics(lyric_url)
                if formatted_lyrics:
                    lyrics_path = os.path.join(lyrics_dir, f"{music_id}.lrc")
                    # 确保以文本格式保存歌词，而不是二进制
                    with open(lyrics_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_lyrics)
                    lyrics_path = os.path.relpath(lyrics_path, assets_dir)
                    logger.info(f"成功获取并保存歌词，共 {len(lyrics_data)} 行")
 
                # 如果是新记录，尝试保存原始JSON歌词数据
                if lyrics_data and isinstance(lyrics_data, list) and len(lyrics_data) > 0:
                    try:
                        # 保存原始歌词JSON数据，方便前端直接使用
                        raw_lyrics_dir = os.path.join(assets_dir, "raw_lyrics")
                        os.makedirs(raw_lyrics_dir, exist_ok=True)
                        raw_lyrics_path = os.path.join(raw_lyrics_dir, f"{music_id}.json")
                        with open(raw_lyrics_path, 'w', encoding='utf-8') as f:
                            json.dump(lyrics_data, f, ensure_ascii=False, indent=2)
                        raw_lyrics_path = os.path.relpath(raw_lyrics_path, assets_dir)
                        logger.info(f"成功保存原始歌词JSON数据")
                    except Exception as e:
                        logger.error(f"保存原始歌词JSON数据失败: {str(e)}")
            except Exception as e:
                logger.error(f"处理歌词失败: {str(e)}")
        
        # 如果有高潮时间和歌词数据，提取高潮段歌词
        chorus_lyrics = ""
        chorus_lyrics_path = ""
        if chorus_start_seconds is not None and chorus_duration_seconds is not None and lyrics_data:
            try:
                logger.info(f"正在提取高潮段歌词: {chorus_start_seconds}秒 - {chorus_start_seconds + chorus_duration_seconds}秒")
                chorus_lyrics = await extract_chorus_lyrics(lyrics_data, chorus_start_seconds, chorus_duration_seconds)
                if chorus_lyrics:
                    chorus_lyrics_path = os.path.join(chorus_lyrics_dir, f"{music_id}_chorus.lrc")
                    with open(chorus_lyrics_path, 'w', encoding='utf-8') as f:
                        f.write(chorus_lyrics)
                    chorus_lyrics_path = os.path.relpath(chorus_lyrics_path, assets_dir)
                    logger.info(f"成功提取并保存高潮段歌词")
                    
                    # 保存高潮段的原始歌词数据（JSON格式）
                    try:
                        # 过滤出高潮段的歌词数据
                        chorus_raw_lyrics = []
                        end_time = chorus_start_seconds + chorus_duration_seconds
                        
                        for line in lyrics_data:
                            line_start = line.get("start_time", 0)
                            line_end = line.get("end_time", 0)
                            
                            # 如果歌词行在高潮段内或与高潮段有交叉，添加到高潮歌词数据中
                            if (line_start >= chorus_start_seconds and line_start < end_time) or \
                               (line_end > chorus_start_seconds and line_end <= end_time) or \
                               (line_start <= chorus_start_seconds and line_end >= end_time):
                                
                                # 复制一份歌词行数据
                                chorus_line = line.copy()
                                # 对时间进行调整，使其相对于高潮段起始时间
                                chorus_line["start_time"] = max(0, line_start - chorus_start_seconds)
                                chorus_line["end_time"] = min(chorus_duration_seconds, line_end - chorus_start_seconds)
                                chorus_raw_lyrics.append(chorus_line)
                        
                        if chorus_raw_lyrics:
                            # 保存高潮段原始歌词JSON
                            chorus_raw_lyrics_path = os.path.join(raw_lyrics_dir, f"{music_id}_chorus.json")
                            with open(chorus_raw_lyrics_path, 'w', encoding='utf-8') as f:
                                json.dump(chorus_raw_lyrics, f, ensure_ascii=False, indent=2)
                            chorus_raw_lyrics_path = os.path.relpath(chorus_raw_lyrics_path, assets_dir)
                            logger.info(f"成功保存高潮段原始JSON歌词数据，共{len(chorus_raw_lyrics)}行")
                        else:
                            logger.warning("未能提取到高潮段的原始歌词数据")
                    except Exception as e:
                        logger.error(f"保存高潮段原始JSON歌词数据失败: {str(e)}")
            except Exception as e:
                logger.error(f"保存高潮歌词失败: {str(e)}")
        
        # 格式化高潮时间段
        if chorus_start_seconds is not None and chorus_duration_seconds is not None:
            end_seconds = chorus_start_seconds + chorus_duration_seconds
            high_peak_time_range = f"{chorus_start_seconds:.3f}秒 - {end_seconds:.3f}秒 (持续{chorus_duration_seconds:.3f}秒)"
        
        # 组装数据
        data_dict = {
            "id": music_id,
            "rank": rank,
            "title": title,
            "author": author,
            "album": album,
            "heat": heat,
            "user_count": user_count,
            "duration": duration,
            "duration_formatted": duration_formatted,
            "is_original": music_info.get("is_original", False),
            "is_commerce_music": music_info.get("is_commerce_music", False),
            "is_aed_music": is_aed_music_flag,
            "has_copyright": has_copyright,
            "can_background_play": can_background_play,
            "update_time": current_datetime,
            "files": {
                "cover_image": cover_image_path,
                "audio": audio_path,
                "lyrics": lyrics_path,
            },
            "high_peak": {
                "time_range": high_peak_time_range,
                "start_seconds": chorus_start_seconds,
                "duration_seconds": chorus_duration_seconds
            },
            "tags": music_tags,
            "music_info": {
                "lyric_url": music_info.get("lyric_url", "")
            },
            "audio_info": {
                "is_full_audio": is_full_audio,   # 添加标记，指示是否为完整音频
                "audio_type": "full" if is_full_audio else "chorus",  # 添加明确的音频类型标记
                "has_chorus_segment": chorus_path is not None and len(chorus_path) > 0  # 标记是否有高潮片段
            }
        }
        
        # 添加高潮数据（如果有）
        if "chorus_path" in locals() and chorus_path:
            data_dict["files"]["chorus"] = chorus_path
        
        if "chorus_lyrics_path" in locals() and chorus_lyrics_path:
            data_dict["files"]["chorus_lyrics"] = chorus_lyrics_path
            
        # 添加原始歌词JSON路径（如果有）
        if "raw_lyrics_path" in locals() and raw_lyrics_path:
            data_dict["files"]["raw_lyrics"] = raw_lyrics_path
            
        # 添加高潮段原始JSON歌词路径（如果有）
        if "chorus_raw_lyrics_path" in locals() and chorus_raw_lyrics_path:
            data_dict["files"]["chorus_raw_lyrics"] = chorus_raw_lyrics_path
        
        # 保存歌词URL列表（如果有的话）
        if music_info.get("lyric_url_list"):
            data_dict["music_info"]["lyric_url_list"] = music_info["lyric_url_list"]
        
        # 保存JSON数据
        json_path = os.path.join(assets_dir, f"{music_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)
            
        # 同时更新一个总的data.json，包含所有音乐信息的列表
        return data_dict
    except Exception as e:
        logger.error(f"分析和保存音乐失败: {str(e)}")
        logger.exception("详细错误信息")
        return None

async def save_all_music_data(musics):
    """保存所有音乐数据
    
    Args:
        musics: 音乐列表
    """
    if not musics:
        logger.warning("没有音乐数据需要处理")
        return
        
    try:
        # 创建assets目录
        assets_dir = os.path.join("assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        all_music_data = []
        
        # 处理每一首音乐
        for i, music in enumerate(musics):
            rank = i + 1
            logger.info(f"处理第{rank}名音乐: {music.get('music_info', {}).get('title', '未知')}")
            music_data = await analyze_and_save_music(music, rank)
            if music_data:
                all_music_data.append(music_data)
                
        # 保存总的data.json
        if all_music_data:
            data_json_path = os.path.join(assets_dir, "data.json")
            with open(data_json_path, 'w', encoding='utf-8') as f:
                json_data = {
                    "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "count": len(all_music_data),
                    "musics": all_music_data
                }
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存全部音乐数据到 {data_json_path}，共 {len(all_music_data)} 首")
    except Exception as e:
        logger.error(f"保存所有音乐数据失败: {str(e)}")
        logger.exception("详细错误信息")

def clear_assets_directory():
    """清空assets文件夹"""
    assets_dir = os.path.join("assets")
    if os.path.exists(assets_dir):
        logger.info(f"正在清空assets文件夹: {assets_dir}")
        # 删除整个目录及其所有内容
        shutil.rmtree(assets_dir)
    
    # 重新创建目录
    os.makedirs(assets_dir, exist_ok=True)
    logger.info(f"已清空并重新创建assets文件夹")

def run():
    # 清空assets文件夹
    clear_assets_directory()
    
    # 获取数据
    dy = Douyin()
    musics = None
    # 音乐
    musics, resp = dy.get_hot_music()
    save_raw_response(resp, 'hot-music')
    time.sleep(1)

    # 保存音乐数据和文件
    asyncio.run(save_all_music_data(musics))


if __name__ == "__main__":
    try:
        run()
    except:
        logger.exception('run failed')
