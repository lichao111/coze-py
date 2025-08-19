import pyaudio
import wave
import time

# 音频参数设置
CHUNK = 1024  # 每次读取的音频块大小
FORMAT = pyaudio.paInt16  # 音频格式 (16位)
CHANNELS = 1  # 单声道
RATE = 44100  # 采样率 44.1kHz
RECORD_SECONDS = 10  # 录音时长(秒)
OUTPUT_FILENAME = "recording.wav"  # 输出文件名

def record_audio():
    """录音函数"""
    # 初始化PyAudio
    p = pyaudio.PyAudio()
    
    print(f"开始录音，时长: {RECORD_SECONDS} 秒...")
    print("请开始说话...")
    
    # 打开音频流
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    frames = []
    
    # 录音循环
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        
        # 显示进度
        progress = (i + 1) / (RATE / CHUNK * RECORD_SECONDS) * 100
        if i % (RATE // CHUNK) == 0:  # 每秒更新一次
            print(f"录音进度: {progress:.0f}%")
    
    print("录音完成!")
    
    # 停止和关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 保存录音文件
    save_audio(frames)

def save_audio(frames):
    """保存音频文件"""
    print(f"正在保存音频文件: {OUTPUT_FILENAME}")
    
    # 创建WAV文件
    wf = wave.open(OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"音频文件已保存: {OUTPUT_FILENAME}")

def list_audio_devices():
    """列出可用的音频设备"""
    p = pyaudio.PyAudio()
    print("可用的音频输入设备:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"设备 {i}: {info['name']} - 输入通道数: {info['maxInputChannels']}")
    p.terminate()

def main():
    try:
        # 显示可用设备(可选)
        list_audio_devices()
        print("-" * 50)
        
        # 开始录音
        record_audio()
        
    except Exception as e:
        print(f"录音过程中发生错误: {e}")
        print("请确保:")
        print("1. 已安装 pyaudio: pip install pyaudio")
        print("2. 麦克风设备正常工作")
        print("3. 系统音频权限已开启")

if __name__ == "__main__":
    main()