# 告警音频文件说明

## 当前状态

`alert.mp3.txt` 是一个占位符文件，需要替换为真实的音频文件。

## 音频要求

- **格式**：MP3
- **时长**：1-3 秒
- **音量**：适中（不要太刺耳）
- **用途**：风控告警提示音

## 获取方式

### 方案 1：使用免费音效库（推荐）

1. **Freesound.org**
   - 网址：https://freesound.org/
   - 搜索关键词：`alert`, `notification`, `warning`
   - 选择 Creative Commons 0 (CC0) 许可的音频

2. **Zapsplat.com**
   - 网址：https://www.zapsplat.com/
   - 免费注册后可下载
   - 搜索：`alert sound`, `notification beep`

3. **Mixkit.co**
   - 网址：https://mixkit.co/free-sound-effects/
   - 完全免费，无需注册
   - 分类：Notifications & Alerts

### 方案 2：使用系统音效

可以从操作系统的系统音效中提取：

**macOS**：
```bash
# 系统音效位置
/System/Library/Sounds/

# 推荐音效
- Basso.aiff (低沉警告音)
- Funk.aiff (轻快提示音)
- Glass.aiff (清脆提示音)
- Ping.aiff (简短提示音)
- Sosumi.aiff (经典提示音)
```

**转换为 MP3**：
```bash
# 使用 ffmpeg 转换
ffmpeg -i /System/Library/Sounds/Basso.aiff -codec:a libmp3lame -qscale:a 2 alert.mp3
```

### 方案 3：在线生成

使用在线音频生成工具：
- **Beepbox.co**：https://www.beepbox.co/
- **Audacity**：免费音频编辑软件，可以生成简单的提示音

## 安装步骤

1. 下载或生成音频文件
2. 重命名为 `alert.mp3`
3. 替换当前的 `alert.mp3.txt`
4. 测试音频播放

## 测试方法

在浏览器控制台中测试：

```javascript
const audio = new Audio('/alert.mp3')
audio.play()
```

## 注意事项

1. **文件大小**：建议 < 100KB
2. **浏览器兼容性**：MP3 格式所有现代浏览器都支持
3. **音量控制**：可以在代码中调整音量（0.0 - 1.0）

```typescript
const audio = new Audio('/alert.mp3')
audio.volume = 0.5  // 50% 音量
audio.play()
```

## 临时解决方案

如果暂时没有音频文件，可以使用 Web Audio API 生成简单的提示音：

```typescript
function playBeep() {
  const audioContext = new AudioContext()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()
  
  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)
  
  oscillator.frequency.value = 800  // 频率 (Hz)
  oscillator.type = 'sine'  // 波形类型
  
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
  
  oscillator.start(audioContext.currentTime)
  oscillator.stop(audioContext.currentTime + 0.5)
}
```

---

**创建时间**：2026-04-13  
**状态**：待处理
