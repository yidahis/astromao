#!/usr/bin/env python3
import wave
import numpy as np

# 创建测试音频文件
sample_rate = 16000
duration = 1  # 1秒
t = np.linspace(0, duration, sample_rate * duration, False)
frequency = 440  # A4音符
audio = np.sin(frequency * 2 * np.pi * t) * 0.3
audio_int = (audio * 32767).astype(np.int16)

with wave.open('test_audio.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # 单声道
    wav_file.setsampwidth(2)  # 16位
    wav_file.setframerate(sample_rate)  # 采样率
    wav_file.writeframes(audio_int.tobytes())

print('Created test_audio.wav')
print(f'File size: {len(audio_int.tobytes())} bytes')