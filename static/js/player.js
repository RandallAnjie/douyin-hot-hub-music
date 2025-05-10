/**
 * 解析歌词字符串
 * 得到一个歌词对象的数组
 * 每个歌词对象：
 * {time:开始时间, words: 歌词内容}
 */
function parseLrc() {
  console.log('解析LRC格式歌词，长度:', lrc.length);
  // 确保lrc是字符串
  if (!lrc || typeof lrc !== 'string' || lrc.trim() === '') {
    console.error('歌词为空或格式错误', lrc);
    return [{time: 0, words: '暂无歌词或歌词格式错误'}];
  }
  
  // 检查是否是JSON格式误传入
  if (lrc.trim().startsWith('[{') && lrc.trim().endsWith('}]')) {
    console.warn('检测到可能是JSON格式歌词被当作LRC处理，尝试解析JSON');
    try {
      const jsonData = JSON.parse(lrc);
      if (Array.isArray(jsonData) && jsonData.length > 0) {
        console.log('成功解析为JSON数据，转为LRC格式处理');
        // 将JSON格式转为LRC格式
        let lrcContent = '';
        jsonData.forEach(item => {
          const time = item.start_time || item.timeId || item.time || 0;
          const content = item.content || item.text || item.words || '';
          const minutes = Math.floor(time / 60);
          const seconds = time % 60;
          const timeStr = `[${minutes.toString().padStart(2, '0')}:${seconds.toFixed(2).padStart(5, '0')}]`;
          lrcContent += `${timeStr}${content}\n`;
        });
        
        // 更新lrc内容
        lrc = lrcContent;
      }
    } catch (e) {
      console.error('尝试解析JSON格式失败，继续按LRC处理', e);
    }
  }
  
  var lines = lrc.split('\n');
  console.log(`歌词行数: ${lines.length}`);
  
  var result = []; // 歌词对象数组
  for (var i = 0; i < lines.length; i++) {
    var str = lines[i].trim();
    if (!str) continue; // 跳过空行
    
    if (str.indexOf('[') < 0 || str.indexOf(']') < 0) {
      console.warn(`第${i+1}行格式不符合LRC要求:`, str);
      continue;
    }
    
    try {
      var parts = str.split(']');
      var timeStr = parts[0].substring(1);
      var obj = {
        time: parseTime(timeStr),
        words: parts[1] || '',
      };
      result.push(obj);
    } catch (e) {
      console.error(`解析第${i+1}行出错:`, e, str);
    }
  }
  
  // 如果没有解析出任何歌词，添加一个默认项
  if (result.length === 0) {
    result.push({time: 0, words: '暂无有效歌词'});
  }
  
  // 根据时间排序
  result.sort((a, b) => a.time - b.time);
  
  console.log(`歌词解析完成，有效行数: ${result.length}`);
  return result;
}

/**
 * 将一个时间字符串解析为数字（秒）
 */
function parseTime(timeStr) {
  try {
    // 添加输入日志
    console.log('解析时间:', timeStr);
    
    // 检查时间字符串格式
    if (!timeStr || typeof timeStr !== 'string') {
      console.error('无效的时间字符串:', timeStr);
      return 0;
    }
    
    var parts = timeStr.split(':');
    if (parts.length < 2) {
      console.error('时间格式不正确 (需要 分:秒 格式):', timeStr);
      return 0;
    }
    
    // 解析分钟和秒钟
    let minutes = parseFloat(parts[0]) || 0;
    let seconds = 0;
    
    // 检查分钟部分是否为有效数字
    if (isNaN(minutes)) {
      console.error('分钟解析失败:', parts[0]);
      minutes = 0;
    }
    
    // 检查秒钟部分是否包含小数点
    if (parts[1].includes('.')) {
      seconds = parseFloat(parts[1]) || 0;
    } else {
      // 没有小数点，按整数处理
      seconds = parseInt(parts[1]) || 0;
    }
    
    // 检查秒钟部分是否为有效数字
    if (isNaN(seconds)) {
      console.error('秒钟解析失败:', parts[1]);
      seconds = 0;
    }
    
    const result = minutes * 60 + seconds;
    console.log(`解析结果: ${minutes}分 + ${seconds}秒 = ${result}秒`);
    return result;
  } catch (e) {
    console.error('解析时间出错:', timeStr, e);
    return 0;
  }
}

// 初始化全局变量
let lrc = ''; // 歌词内容
let lrcData = []; // 解析后的歌词数据
let doms = {}; // DOM元素集合

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  console.log('歌词播放器DOM已加载');
  
  // 获取需要的 dom
  doms = {
    audio: document.querySelector('audio'),
    ul: document.querySelector('.container ul'),
    container: document.querySelector('.container'),
    status_pic: document.getElementById('status_pic'),
    discpointer_pic: document.getElementById('discpointer_pic'),
  };
  
  // 初始化播放器
  initPlayer();
  
  // 修正favicon
  const favicon = document.querySelector('link[rel="shortcut icon"]');
  if (favicon) {
    favicon.href = './img/music_disc.png';
  }
});

/**
 * 初始化播放器
 */
function initPlayer() {
  console.log('播放器初始化中...');
  
  // 设置音频更新事件
  if (doms.audio) {
    doms.audio.addEventListener('timeupdate', setOffset);
    
    // 添加音频就绪事件监听
    doms.audio.addEventListener('canplay', function() {
      console.log('音频已就绪，可以播放');
      // 确保当前时间为0，以正确显示第一句歌词
      if (doms.audio.currentTime > 0.1) {
        doms.audio.currentTime = 0;
      }
      setOffset(); // 确保歌词位置正确
    });
    
    // 添加音频元数据加载完成事件监听
    doms.audio.addEventListener('loadedmetadata', function() {
      console.log('音频元数据已加载，时长:', doms.audio.duration);
      // 确保当前时间为0，以正确显示第一句歌词
      doms.audio.currentTime = 0;
      setOffset();
    });
    
    // 添加播放开始事件监听
    doms.audio.addEventListener('play', function() {
      console.log('音频开始播放');
      setOffset(); // 确保歌词从头开始显示
    });
  } else {
    console.error('找不到音频元素');
  }
}

/**
 * 设置歌词内容并触发解析和渲染
 * @param {string} lyricContent - 歌词内容文本
 */
function setLyricContent(lyricContent) {
  console.log('设置歌词内容，长度:', lyricContent ? lyricContent.length : 0);
  
  // 预先保存音频状态
  const wasPlaying = doms.audio && !doms.audio.paused;
  
  if (!lyricContent || lyricContent.trim() === '') {
    console.warn('歌词内容为空，使用默认歌词');
    lrcData = [{time: 0, words: '暂无歌词'}];
    
    // 清空现有的歌词元素
    if (doms.ul) {
      doms.ul.innerHTML = '';
      
      // 创建新的歌词元素
      createLrcElements();
      
      // 确保从头开始显示歌词
      if (doms.audio) {
        if (wasPlaying) {
          // 如果之前在播放，暂停后再设置时间
          doms.audio.pause();
        }
        doms.audio.currentTime = 0;
      }
      
      // 初始化偏移
      setOffset();
      
      // 如果之前在播放，恢复播放
      if (wasPlaying && doms.audio) {
        doms.audio.play();
      }
    }
    return;
  }
  
  // 尝试判断歌词是否是JSON格式
  let isJsonFormat = false;
  try {
    // 检查是否为JSON格式
    if (lyricContent.trim().startsWith('[') && lyricContent.trim().endsWith(']')) {
      const parsedData = JSON.parse(lyricContent);
      if (Array.isArray(parsedData) && parsedData.length > 0) {
        // 检查是否包含常见的JSON歌词格式字段
        if (parsedData[0].start_time !== undefined || 
            parsedData[0].timeId !== undefined ||
            parsedData[0].time !== undefined) {
          console.log('检测到JSON格式歌词数据');
          isJsonFormat = true;
          
          // 检查第一个和最后一个时间点，帮助调试
          const firstItem = parsedData[0];
          const lastItem = parsedData[parsedData.length - 1];
          console.log('第一个歌词时间点:', firstItem);
          console.log('最后一个歌词时间点:', lastItem);
          
          // 确定时间单位：检查最后一个和第一个时间点的差值
          let timeUnit = 1; // 默认为秒
          let maxTime = 0;
          
          // 寻找最大时间值，用于判断单位
          parsedData.forEach(item => {
            const itemTime = item.start_time !== undefined ? item.start_time : 
                           (item.timeId !== undefined ? item.timeId : 
                            (item.time !== undefined ? item.time : 0));
            
            if (parseFloat(itemTime) > maxTime) {
              maxTime = parseFloat(itemTime);
            }
          });
          
          console.log('最大时间值:', maxTime);
          
          // 如果最大时间超过10分钟（600秒），可能是毫秒单位
          if (maxTime > 600) {
            timeUnit = 1000;
            console.log('检测到可能是毫秒单位，将转换为秒');
          } else {
            console.log('检测到可能是秒单位，不进行转换');
          }
          
          // 获取高潮信息
          const chorusInfo = window.chorusInfo || {};
          const isChorus = chorusInfo.isChorus || false;
          const chorusStartSeconds = chorusInfo.startSeconds;
          const chorusDurationSeconds = chorusInfo.durationSeconds;
          
          console.log('歌词处理：', isChorus ? '高潮片段模式' : '正常播放模式');
          
          // 准备处理高潮歌词
          let processedLyrics = parsedData.slice(); // 创建一个副本，不直接修改原数据
          
          // 如果是高潮片段，且有高潮段起始时间信息，需要调整歌词时间
          if (isChorus && chorusStartSeconds !== undefined) {
            console.log(`根据高潮信息调整歌词时间偏移：开始于${chorusStartSeconds}秒，持续${chorusDurationSeconds}秒`);
            
            // 准备筛选高潮部分的歌词
            console.log('开始筛选高潮部分歌词');
            
            // 筛选出高潮部分的歌词，只保留在高潮时间范围内的歌词
            let filteredLyrics = [];
            const chorusEndSeconds = chorusStartSeconds + chorusDurationSeconds;
            
            console.log(`筛选歌词范围：${chorusStartSeconds}秒 - ${chorusEndSeconds}秒`);
            
            // 筛选并调整歌词时间
            for (let i = 0; i < processedLyrics.length; i++) {
              const item = processedLyrics[i];
              let time = item.start_time !== undefined ? parseFloat(item.start_time) : 
                        (item.timeId !== undefined ? parseFloat(item.timeId) : 
                         (item.time !== undefined ? parseFloat(item.time) : 0));
              
              // 如果单位是毫秒，转换为秒
              if (timeUnit === 1000) {
                time = time / 1000;
              }
              
              // 歌词行的结束时间（如果有）或估计约5秒
              let endTime = item.end_time ? parseFloat(item.end_time) / (timeUnit === 1000 ? 1000 : 1) : time + 5;
              
              // 检查歌词是否在高潮范围内
              // 1. 开始时间在高潮范围内
              // 2. 结束时间在高潮范围内
              // 3. 歌词包含了整个高潮段
              if ((time >= chorusStartSeconds && time < chorusEndSeconds) || 
                  (endTime > chorusStartSeconds && endTime <= chorusEndSeconds) || 
                  (time <= chorusStartSeconds && endTime >= chorusEndSeconds)) {
                
                console.log(`歌词行在高潮范围内: ${time}秒, "${item.content || item.text || item.words || ''}"`);
                
                // 创建新的歌词项，调整时间为相对于高潮开始的时间
                let adjustedItem = { ...item };
                
                // 调整时间 - 确保时间从0开始正确递增
                const adjustedTime = Math.max(0, time - chorusStartSeconds);
                
                if (adjustedItem.start_time !== undefined) {
                  adjustedItem.start_time = adjustedTime;
                } else if (adjustedItem.timeId !== undefined) {
                  adjustedItem.timeId = adjustedTime;
                } else if (adjustedItem.time !== undefined) {
                  adjustedItem.time = adjustedTime;
                }
                
                // 如果有结束时间，也进行调整
                if (adjustedItem.end_time !== undefined) {
                  adjustedItem.end_time = Math.min(chorusDurationSeconds, endTime - chorusStartSeconds);
                }
                
                // 记录原始时间和调整后的时间，便于调试
                console.log(`歌词时间调整: ${time}秒 -> ${adjustedTime}秒`);
                
                filteredLyrics.push(adjustedItem);
              }
            }
            
            console.log(`高潮部分筛选出${filteredLyrics.length}行歌词，原始歌词共${processedLyrics.length}行`);
            
            // 确保筛选后的歌词按照时间顺序排序
            if (filteredLyrics.length > 0) {
              filteredLyrics.sort((a, b) => {
                const timeA = a.start_time !== undefined ? a.start_time : 
                             (a.timeId !== undefined ? a.timeId : 
                              (a.time !== undefined ? a.time : 0));
                const timeB = b.start_time !== undefined ? b.start_time : 
                             (b.timeId !== undefined ? b.timeId : 
                              (b.time !== undefined ? b.time : 0));
                return timeA - timeB;
              });
              
              // 确保第一句歌词时间为0，避免开始就跳过歌词
              if (filteredLyrics.length > 0) {
                const firstLyric = filteredLyrics[0];
                const firstTime = firstLyric.start_time !== undefined ? firstLyric.start_time : 
                                (firstLyric.timeId !== undefined ? firstLyric.timeId : 
                                 (firstLyric.time !== undefined ? firstLyric.time : 0));
                
                // 如果第一句歌词时间大于0，添加一个时间为0的空白歌词
                if (firstTime > 0.5) {
                  console.log(`第一句歌词时间为${firstTime}秒，添加一个时间为0的过渡歌词`);
                  const transitionLyric = { ...firstLyric };
                  
                  if (transitionLyric.start_time !== undefined) {
                    transitionLyric.start_time = 0;
                  } else if (transitionLyric.timeId !== undefined) {
                    transitionLyric.timeId = 0;
                  } else if (transitionLyric.time !== undefined) {
                    transitionLyric.time = 0;
                  }
                  
                  // 保留原始歌词内容
                  if (transitionLyric.content !== undefined) {
                    transitionLyric.content = `等待高潮...` + (transitionLyric.content || '');
                  } else if (transitionLyric.text !== undefined) {
                    transitionLyric.text = `等待高潮...` + (transitionLyric.text || '');
                  } else if (transitionLyric.words !== undefined) {
                    transitionLyric.words = `等待高潮...` + (transitionLyric.words || '');
                  }
                  
                  filteredLyrics.unshift(transitionLyric);
                }
              }
              
              // 使用筛选后的歌词替换处理后的数据
              processedLyrics = filteredLyrics;
              console.log('成功替换为高潮部分歌词，已确保时间正确排序');
              
              // 输出最终的歌词时间，用于调试
              for (let i = 0; i < Math.min(5, processedLyrics.length); i++) {
                const item = processedLyrics[i];
                const time = item.start_time !== undefined ? item.start_time : 
                           (item.timeId !== undefined ? item.timeId : 
                            (item.time !== undefined ? item.time : 0));
                console.log(`歌词${i}: 时间=${time}秒, 内容="${item.content || item.text || item.words || ''}"`);
              }
            } else {
              console.warn('未找到高潮部分对应的歌词，将使用全部歌词并调整时间偏移');
              
              // 如果没找到匹配的歌词，则对所有歌词进行时间偏移调整
              processedLyrics = processedLyrics.map(item => {
                let time = item.start_time !== undefined ? parseFloat(item.start_time) : 
                         (item.timeId !== undefined ? parseFloat(item.timeId) : 
                          (item.time !== undefined ? parseFloat(item.time) : 0));
                
                // 如果单位是毫秒，转换为秒
                if (timeUnit === 1000) {
                  time = time / 1000;
                }
                
                // 创建调整后的对象
                let adjustedItem = { ...item };
                
                // 查找原始歌词中的最小时间，用于计算相对偏移
                let minOriginalTime = Math.min(...processedLyrics.map(lyric => {
                  let t = lyric.start_time !== undefined ? parseFloat(lyric.start_time) : 
                         (lyric.timeId !== undefined ? parseFloat(lyric.timeId) : 
                          (lyric.time !== undefined ? parseFloat(lyric.time) : 0));
                  if (timeUnit === 1000) t = t / 1000;
                  return t;
                }));
                
                // 相对于首个歌词的时间偏移，而不是减去高潮开始时间
                // 这样保持了歌词间的相对时间间隔
                const relativeTime = Math.max(0, time - minOriginalTime);
                
                // 按比例缩放到高潮持续时间内
                const scaleFactor = chorusDurationSeconds / Math.max(1, processedLyrics[processedLyrics.length-1].start_time - minOriginalTime);
                const scaledTime = relativeTime * scaleFactor;
                
                console.log(`调整歌词时间: 原始${time}秒, 相对${relativeTime}秒, 缩放后${scaledTime}秒`);
                
                // 应用调整后的时间
                if (adjustedItem.start_time !== undefined) {
                  adjustedItem.start_time = scaledTime;
                } else if (adjustedItem.timeId !== undefined) {
                  adjustedItem.timeId = scaledTime;
                } else if (adjustedItem.time !== undefined) {
                  adjustedItem.time = scaledTime;
                }
                
                return adjustedItem;
              });
              
              // 确保第一句歌词时间为0
              const firstItem = processedLyrics[0];
              const firstTime = firstItem.start_time !== undefined ? firstItem.start_time : 
                              (firstItem.timeId !== undefined ? firstItem.timeId : 
                              (firstItem.time !== undefined ? firstItem.time : 0));
                              
              if (firstTime > 0.1) {
                console.log(`第一句歌词时间(${firstTime}秒)不为0，将所有歌词时间减去这个值以确保从0开始`);
                processedLyrics = processedLyrics.map(item => {
                  let adjustedItem = { ...item };
                  
                  // 时间调整，确保从0开始
                  if (adjustedItem.start_time !== undefined) {
                    adjustedItem.start_time = Math.max(0, adjustedItem.start_time - firstTime);
                  } else if (adjustedItem.timeId !== undefined) {
                    adjustedItem.timeId = Math.max(0, adjustedItem.timeId - firstTime);
                  } else if (adjustedItem.time !== undefined) {
                    adjustedItem.time = Math.max(0, adjustedItem.time - firstTime);
                  }
                  
                  return adjustedItem;
                });
              }
            }
            
            // 根据调整后的时间重新排序
            processedLyrics.sort((a, b) => {
              const timeA = a.start_time !== undefined ? a.start_time : 
                           (a.timeId !== undefined ? a.timeId : 
                            (a.time !== undefined ? a.time : 0));
              
              const timeB = b.start_time !== undefined ? b.start_time : 
                           (b.timeId !== undefined ? b.timeId : 
                            (b.time !== undefined ? b.time : 0));
                            
              return parseFloat(timeA) - parseFloat(timeB);
            });
          }
          
          // 转换为统一的内部表示形式
          lrcData = processedLyrics.map(item => {
            // 确定时间
            let time = 0;
            if (item.start_time !== undefined) {
              time = parseFloat(item.start_time);
            } else if (item.timeId !== undefined) {
              time = parseFloat(item.timeId);
            } else if (item.time !== undefined) {
              time = parseFloat(item.time);
            }
            
            // 确定歌词文本
            const text = item.content || item.text || item.words || '';
            
            // 应用时间单位转换
            if (timeUnit === 1000) {
              time = time / 1000;
            }
            
            return {
              time: time,
              words: text
            };
          });
          
          // 根据时间排序
          lrcData.sort((a, b) => a.time - b.time);
          
          // 打印排序后的前5个时间点，用于调试
          console.log('解析后的前5个歌词时间点:', lrcData.slice(0, 5).map(item => item.time));
          if (lrcData.length > 5) {
            console.log('解析后的最后5个歌词时间点:', lrcData.slice(-5).map(item => item.time));
          }
          
          console.log('JSON歌词解析完成，共', lrcData.length, '行');
        }
      }
    }
  } catch (e) {
    console.error('解析JSON格式歌词失败:', e);
    isJsonFormat = false;
  }
  
  // 如果不是JSON格式，按照传统LRC格式处理
  if (!isJsonFormat) {
    lrc = lyricContent;
    // 解析歌词
    lrcData = parseLrc();
  }
  
  // 清空现有的歌词元素
  if (doms.ul) {
    doms.ul.innerHTML = '';
    
    // 创建新的歌词元素
    createLrcElements();
    
    // 确保从头开始显示歌词
    if (doms.audio) {
      doms.audio.currentTime = 0;
    }
    
    // 初始化偏移
    setOffset();
  } else {
    console.error('找不到歌词容器元素');
  }
}

/**
 * 计算出，在当前播放器播放到第几秒的情况下
 * lrcData数组中，应该高亮显示的歌词下标
 * 如果没有任何一句歌词需要显示，则得到-1
 */
function findIndex() {
  if (!doms.audio || !lrcData.length) return 0;
  
  // 播放器当前时间
  var curTime = doms.audio.currentTime;
  console.log('当前播放时间:', curTime, '秒');
  
  // 如果当前时间为0或非常小的值，返回第一句歌词
  if (curTime < 0.1) {
    console.log('播放时间接近0，显示第一句歌词');
    return 0;
  }
  
  // 检查第一个歌词的时间戳，如果当前时间小于第一个歌词时间，返回第一句
  if (lrcData[0] && curTime < lrcData[0].time) {
    console.log('当前时间小于第一个歌词时间点，显示第一句歌词');
    return 0;
  }
  
  // 检查歌词时间范围
  console.log('歌词时间范围:', lrcData[0]?.time, '到', lrcData[lrcData.length-1]?.time);
  
  // 找到当前时间对应的歌词
  let index = 0;
  for (var i = 0; i < lrcData.length; i++) {
    if (curTime >= lrcData[i].time) {
      index = i;
    } else {
      break;
    }
  }
  
  console.log('找到当前歌词索引:', index, ', 对应时间点:', lrcData[index]?.time);
  return index;
}

// 界面

/**
 * 创建歌词元素 li
 */
function createLrcElements() {
  if (!doms.ul) return;
  
  console.log('创建歌词元素，共', lrcData.length, '行');
  var frag = document.createDocumentFragment(); // 文档片段
  for (var i = 0; i < lrcData.length; i++) {
    var li = document.createElement('li');
    li.textContent = lrcData[i].words;
    frag.appendChild(li); // 改动了 dom 树
  }
  doms.ul.appendChild(frag);
  
  // 计算最大偏移量
  if (doms.container && doms.ul.children.length > 0) {
    containerHeight = doms.container.clientHeight;
    liHeight = doms.ul.children[0].clientHeight;
    maxOffset = containerHeight - doms.ul.clientHeight;
  }
}

// 初始值
var containerHeight = 0;
var liHeight = 0;
var maxOffset = 0;

/**
 * 设置 ul 元素的偏移量
 */
function setOffset() {
  if (!doms.ul || !doms.container) return;
  
  console.log('===== 开始设置歌词偏移 =====');
  
  // 获取当前应高亮的歌词索引
  let index;
  
  // 1. 针对暂停状态的特殊处理
  if (!doms.audio) {
    console.log('音频元素不存在，显示第一句歌词');
    index = 0;
  } else if (doms.audio.paused) {
    // 暂停状态：如果当前时间很小，显示第一句，否则保持当前位置
    if (doms.audio.currentTime < 0.1) {
      console.log('暂停且时间接近0，显示第一句歌词');
      index = 0;
    } else {
      console.log('暂停状态，使用findIndex计算当前歌词位置');
      index = findIndex();
    }
  } 
  // 2. 针对播放状态的处理
  else if (doms.audio.currentTime < 0.1) {
    console.log('播放中但时间接近0，显示第一句歌词');
    index = 0;
  } else {
    console.log('正常播放中，使用findIndex计算当前歌词位置');
    index = findIndex();
  }
  
  // 确保索引有效
  if (index < 0) {
    console.log('索引小于0，重置为0');
    index = 0;
  }
  if (index >= lrcData.length) {
    console.log('索引超出范围，重置为最后一行');
    index = lrcData.length - 1;
  }
  
  console.log('最终使用的歌词索引:', index);
  
  // 计算偏移量 - 使歌词保持在容器中央
  var offset = containerHeight / 2 - liHeight * index;
  
  // 处理特殊情况：
  // 1. 如果是最后几句歌词，不要让歌词显示在底部，保持居中显示
  const remainingLines = lrcData.length - index - 1; // 当前行之后剩余的行数
  const linesNeededForCenter = Math.floor(containerHeight / (2 * liHeight)); // 居中显示需要的行数
  
  // 如果剩余行数少于居中所需行数，调整偏移量确保歌词居中显示
  if (remainingLines < linesNeededForCenter) {
    console.log(`接近歌曲结尾，调整偏移保持居中显示。剩余行数:${remainingLines}, 居中所需行数:${linesNeededForCenter}`);
    // 计算一个新的偏移量，使最后一行位于容器中央偏下的位置
    const lastLineIndex = lrcData.length - 1;
    const idealPosition = containerHeight / 2 + liHeight; // 中央偏下位置
    const newOffset = idealPosition - liHeight * lastLineIndex;
    
    // 逐渐过渡到新的偏移量，避免突变
    // 当播放到最后几行时，越来越接近新的偏移量
    const transitionFactor = Math.min(1, (linesNeededForCenter - remainingLines) / linesNeededForCenter);
    offset = offset * (1 - transitionFactor) + newOffset * transitionFactor;
    console.log(`歌词居中过渡系数: ${transitionFactor.toFixed(2)}, 新偏移量: ${offset.toFixed(2)}`);
  }
  
  // 限制偏移量不超出有效范围
  if (offset < maxOffset) {
    offset = maxOffset;
  }
  
  console.log('计算的偏移量:', offset, 'px');
  doms.ul.style.transform = `translateY(${offset}px)`;
  
  // 去掉之前的 active 样式
  var li = doms.ul.querySelector('.active');
  if (li) {
    li.classList.remove('active');
  }

  if (doms.ul.children[index]) {
    doms.ul.children[index].classList.add('active');
  }
  
  console.log('===== 歌词偏移设置完成 =====');
}

/**
 * 控制播放暂停
 */
function control() {
  if (!doms.audio) return;
  
  console.log('控制播放/暂停，当前状态:', doms.audio.paused ? '暂停' : '播放');
  
  if(doms.audio.paused) {
    // 播放前记住当前时间
    const currentTime = doms.audio.currentTime;
    console.log('开始播放，当前时间:', currentTime);
    
    // 如果当前是在开头，确保歌词从头开始显示
    if (currentTime < 0.1) {
      console.log('当前在起始位置，确保从第一句歌词开始');
      // 重新计算偏移量，确保从第一句歌词开始
      setOffset();
    }
    
    doms.audio.play()
      .then(() => {
        console.log('播放成功');
      })
      .catch(err => {
        console.error('播放失败:', err);
      });
      
    doms.status_pic.style.height = '100px';
    doms.status_pic.style.width = '100px';
    doms.discpointer_pic.style.height = '70px';
    doms.discpointer_pic.style.width = '80px';
    doms.status_pic.style.animation = 'rotate 2s linear infinite';
  } else {
    console.log('暂停播放');
    doms.audio.pause();
    
    console.log('暂停时的播放位置:', doms.audio.currentTime);
    
    doms.status_pic.style.height = '80px';
    doms.status_pic.style.width = '80px';
    doms.discpointer_pic.style.height = '40px';
    doms.discpointer_pic.style.width = '50px';
    doms.status_pic.style.animation = 'none';
    
    // 暂停后不重新计算歌词位置，保持当前显示
  }
}

// 暴露给外部调用的接口
window.playerApi = {
  setLyricContent: setLyricContent
};
