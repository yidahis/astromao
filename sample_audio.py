#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroMao - 示例音频生成器
用于生成测试音频文件，方便测试语音识别功能
"""

import os
import sys
import argparse
import numpy as np
from scipy.io import wavfile
import tempfile

def generate_test_audio(output_path="test_audio.wav", duration=5, sample_rate=16000):
    """
    生成测试音频文件
    
    Args:
        output_path: 输出文件路径
        duration: 音频时长（秒）
        sample_rate: 采样率
    """
    # 生成正弦波音频（模拟语音）
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 创建多个频率的正弦波混合（模拟人声频率范围）
    frequencies = [200, 400, 800, 1600]  # 人声基频和谐波
    audio = np.zeros_like(t)
    
    for freq in frequencies:
        amplitude = 0.1 / len(frequencies)
        audio += amplitude * np.sin(2 * np.pi * freq * t)
    
    # 添加一些噪声使其更真实
    noise = 0.01 * np.random.randn(len(t))
    audio += noise
    
    # 归一化到16位整数范围
    audio = np.clip(audio, -1, 1)
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # 保存为WAV文件
    wavfile.write(output_path, sample_rate, audio_int16)
    print(f"测试音频已生成: {output_path}")
    print(f"时长: {duration}秒, 采样率: {sample_rate}Hz")

def download_sample_audio():
    """
    下载真实的示例音频文件（如果网络可用）
    """
    try:
        import urllib.request
        
        # 一些公开的测试音频URL
        sample_urls = [
            "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
            "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
        ]
        
        for i, url in enumerate(sample_urls):
            try:
                filename = f"sample_{i+1}.wav"
                print(f"正在下载示例音频: {url}")
                urllib.request.urlretrieve(url, filename)
                print(f"下载完成: {filename}")
                return filename
            except Exception as e:
                print(f"下载失败: {e}")
                continue
                
    except ImportError:
        print("urllib不可用，跳过下载")
    
    return None

def create_multi_speaker_audio(output_path="multi_speaker.wav", duration=10):
    """
    创建模拟多说话人的音频文件
    """
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 模拟两个说话人的不同频率特征
    speaker1_freq = [150, 300, 600, 1200]  # 较低频率（男声）
    speaker2_freq = [200, 400, 800, 1600]  # 较高频率（女声）
    
    audio = np.zeros_like(t)
    
    # 前半段：说话人1
    half_duration = duration // 2
    t1 = t[:int(sample_rate * half_duration)]
    for freq in speaker1_freq:
        amplitude = 0.15 / len(speaker1_freq)
        audio[:len(t1)] += amplitude * np.sin(2 * np.pi * freq * t1)
    
    # 后半段：说话人2
    t2 = t[int(sample_rate * half_duration):]
    for freq in speaker2_freq:
        amplitude = 0.15 / len(speaker2_freq)
        audio[int(sample_rate * half_duration):] += amplitude * np.sin(2 * np.pi * freq * (t2 - t2[0]))
    
    # 添加噪声
    noise = 0.02 * np.random.randn(len(t))
    audio += noise
    
    # 归一化
    audio = np.clip(audio, -1, 1)
    audio_int16 = (audio * 32767).astype(np.int16)
    
    wavfile.write(output_path, sample_rate, audio_int16)
    print(f"多说话人测试音频已生成: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AstroMao 示例音频生成器")
    parser.add_argument("--output", "-o", default="test_audio.wav", help="输出文件路径")
    parser.add_argument("--duration", "-d", type=int, default=5, help="音频时长（秒）")
    parser.add_argument("--sample-rate", "-r", type=int, default=16000, help="采样率")
    parser.add_argument("--multi-speaker", action="store_true", help="生成多说话人音频")
    parser.add_argument("--download", action="store_true", help="尝试下载真实示例音频")
    
    args = parser.parse_args()
    
    if args.download:
        downloaded = download_sample_audio()
        if downloaded:
            print(f"可以使用下载的音频文件进行测试: {downloaded}")
            return
    
    if args.multi_speaker:
        create_multi_speaker_audio(args.output, args.duration)
    else:
        generate_test_audio(args.output, args.duration, args.sample_rate)
    
    print(f"\n使用方法:")
    print(f"1. 启动AstroMao服务: python app.py")
    print(f"2. 在浏览器中打开: http://localhost:8001")
    print(f"3. 上传生成的音频文件: {args.output}")

if __name__ == "__main__":
    main()