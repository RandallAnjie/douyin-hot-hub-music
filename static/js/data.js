// 从URL中获取参数
function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

// 获取歌曲ID和类型（普通或高潮）
const musicId = getQueryParam('id');
const musicType = getQueryParam('type') || 'normal'; // 默认为普通播放

// 设置文档标题和图标
document.title = `抖音热门音乐播放器`;

// 获取音频元素
const audioElement = document.querySelector('audio');
// 获取背景元素
const bgElement = document.querySelector('.background');

// 根据参数加载对应的音频和歌词
async function loadMusicData() {
  try {
    // 获取JSON数据
    const response = await fetch(`../assets/${musicId}.json`);
    if (!response.ok) {
      throw new Error('音乐数据加载失败');
    }
    
    const musicData = await response.json();
    
    // 获取高潮部分信息
    const highPeakInfo = musicData.high_peak || {};
    const chorusStartSeconds = highPeakInfo.start_seconds;
    const chorusDurationSeconds = highPeakInfo.duration_seconds;
    
    // 确定音频类型
    const isFullAudio = musicData.audio_info?.is_full_audio !== false;
    const audioType = musicData.audio_info?.audio_type || (isFullAudio ? 'full' : 'chorus');
    
    console.log('歌曲信息:', 
                `类型: ${audioType}`, 
                chorusStartSeconds !== undefined ? 
                `高潮开始于${chorusStartSeconds}秒，持续${chorusDurationSeconds}秒` : 
                '无高潮信息');
    
    // 更新标题，根据实际音频类型和用户选择的播放模式
    document.title = `${musicData.title} - ${musicData.author}`;
    
    // 如果原始音频已经是高潮片段，或者用户选择播放高潮片段
    if (audioType === 'chorus' || musicType === 'chorus') {
      document.title += ' (高潮片段)';
    }
    
    // 更新背景图
    if (musicData.files.cover_image) {
      bgElement.style.background = `linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("../assets/${musicData.files.cover_image}") no-repeat center center fixed`;
      bgElement.style.backgroundSize = 'cover';
    }
    
    // 更新音频源 - 根据音频类型和用户选择的播放模式决定
    let audioPath;
    
    if (musicType === 'chorus' && musicData.files.chorus) {
      // 用户选择播放高潮片段且存在高潮片段文件
      audioPath = `../assets/${musicData.files.chorus}`;
      console.log('播放用户指定的高潮片段');
    } else if (audioType === 'chorus') {
      // 原始音频就是高潮片段
      audioPath = `../assets/${musicData.files.audio}`;
      console.log('原始音频已是高潮片段');
    } else {
      // 播放完整音频
      audioPath = `../assets/${musicData.files.audio}`;
      console.log('播放完整音频');
    }
    
    audioElement.src = audioPath;
    
    // 创建全局变量，存储高潮信息，供player.js使用
    window.chorusInfo = {
      isChorus: audioType === 'chorus' || musicType === 'chorus',
      startSeconds: chorusStartSeconds,
      durationSeconds: chorusDurationSeconds,
      originalAudioIsChorus: audioType === 'chorus'
    };
    
    // 加载歌词
    let lyricsPath;
    let rawLyricsPath;
    
    // 根据播放模式选择相应的歌词文件
    if (musicType === 'chorus' || audioType === 'chorus') {
      // 高潮模式：优先使用高潮部分歌词
      // 包括两种情况：1. 用户选择播放高潮片段 2. 原始音频本身就是高潮片段
      console.log('播放高潮片段，尝试加载高潮歌词');
      
      if (musicData.files.chorus_lyrics) {
        lyricsPath = `../assets/${musicData.files.chorus_lyrics}`;
      }
      
      // 检查是否有高潮片段的原始JSON歌词
      if (musicData.files.chorus_raw_lyrics) {
        rawLyricsPath = `../assets/${musicData.files.chorus_raw_lyrics}`;
      } else {
        // 如果没有特定的高潮原始歌词，尝试用普通原始歌词
        rawLyricsPath = musicData.files.raw_lyrics ? `../assets/${musicData.files.raw_lyrics}` : null;
      }
    } else {
      // 普通模式：使用完整歌词
      if (musicData.files.lyrics) {
        lyricsPath = `../assets/${musicData.files.lyrics}`;
      }
      
      // 普通原始JSON歌词
      rawLyricsPath = musicData.files.raw_lyrics ? `../assets/${musicData.files.raw_lyrics}` : null;
    }
    
    let lyricsContent = '';
    
    // 1. 尝试加载原始JSON歌词数据
    if (rawLyricsPath) {
      try {
        console.log('尝试加载原始JSON歌词:', rawLyricsPath);
        const rawLyricsResponse = await fetch(rawLyricsPath);
        if (rawLyricsResponse.ok) {
          const rawLyricsData = await rawLyricsResponse.json();
          
          // 处理JSON格式歌词 - 直接传递给player.js处理
          if (window.playerApi && typeof window.playerApi.setLyricContent === 'function') {
            console.log('加载原始JSON歌词数据成功, 行数:', rawLyricsData.length);
            // 直接传递JSON对象，而不是字符串
            window.playerApi.setLyricContent(JSON.stringify(rawLyricsData));
            return;
          }
        }
      } catch (error) {
        console.error('加载原始JSON歌词失败:', error);
      }
    }
    
    // 2. 如果原始JSON加载失败，尝试加载LRC文件
    if (lyricsPath) {
      try {
        console.log('尝试加载LRC格式歌词:', lyricsPath);
        const lyricsResponse = await fetch(lyricsPath);
        if (lyricsResponse.ok) {
          lyricsContent = await lyricsResponse.text();
          
          // 传递给player.js处理
          if (window.playerApi && typeof window.playerApi.setLyricContent === 'function') {
            window.playerApi.setLyricContent(lyricsContent);
            console.log('加载LRC歌词文件成功');
            return;
          }
        }
      } catch (error) {
        console.error('加载LRC歌词失败:', error);
      }
    }
    
    // 3. 如果前两种方式都失败，尝试从原始歌词链接获取
    if (musicData.music_info && musicData.music_info.lyric_url) {
      try {
        console.log('尝试从原始链接加载歌词');
        const response = await fetch(musicData.music_info.lyric_url);
        if (response.ok) {
          const data = await response.json();
          
          // 传递给player.js处理
          if (window.playerApi && typeof window.playerApi.setLyricContent === 'function') {
            window.playerApi.setLyricContent(JSON.stringify(data));
            console.log('从原始链接加载歌词成功');
            return;
          }
        }
      } catch (error) {
        console.error('从原始链接加载歌词失败:', error);
      }
    }
    
    // 4. 如果都失败，显示默认歌词
    if (window.playerApi && typeof window.playerApi.setLyricContent === 'function') {
      window.playerApi.setLyricContent('[00:00.000] 暂无歌词');
      console.log('使用默认歌词');
    }
    
  } catch (error) {
    console.error('加载音乐数据失败:', error);
    
    // 显示错误消息
    if (window.playerApi && typeof window.playerApi.setLyricContent === 'function') {
      window.playerApi.setLyricContent('[00:00.000] 加载歌词失败');
    }
  }
}

// 页面加载时执行
window.addEventListener('DOMContentLoaded', loadMusicData);