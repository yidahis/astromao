#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

"""
AstroMao Test Script

测试脚本，用于验证AstroMao应用的各项功能。
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import aiohttp
import requests


class AstroMaoTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name, success, message="", duration=0):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration
        })
    
    def test_server_health(self):
        """测试服务器健康状态"""
        print("\n🔍 Testing server health...")
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Server Health Check", True, 
                                f"Server is healthy, models loaded: {data.get('models_loaded')}", duration)
                    return True
                else:
                    self.log_test("Server Health Check", False, 
                                f"Server unhealthy: {data}", duration)
                    return False
            else:
                self.log_test("Server Health Check", False, 
                            f"HTTP {response.status_code}", duration)
                return False
        
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test("Server Health Check", False, 
                        f"Connection error: {e}", duration)
            return False
    
    def test_web_interface(self):
        """测试Web界面"""
        print("\n🌐 Testing web interface...")
        start_time = time.time()
        
        try:
            response = requests.get(self.base_url, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                if "AstroMao" in content and "语音识别" in content:
                    self.log_test("Web Interface", True, 
                                "Web page loaded successfully", duration)
                    return True
                else:
                    self.log_test("Web Interface", False, 
                                "Web page content incorrect", duration)
                    return False
            else:
                self.log_test("Web Interface", False, 
                            f"HTTP {response.status_code}", duration)
                return False
        
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test("Web Interface", False, 
                        f"Connection error: {e}", duration)
            return False
    
    def create_test_audio(self):
        """创建测试音频文件（简单的正弦波）"""
        try:
            import numpy as np
            import wave
            
            # 生成简单的测试音频（1秒，440Hz正弦波）
            sample_rate = 16000
            duration = 1.0
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
            audio_data = (audio_data * 32767).astype(np.int16)
            
            test_file = "test_audio.wav"
            with wave.open(test_file, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return test_file
        
        except ImportError:
            print("⚠️  numpy not available, skipping audio generation test")
            return None
        except Exception as e:
            print(f"⚠️  Failed to create test audio: {e}")
            return None
    
    def test_audio_recognition(self):
        """测试音频识别功能"""
        print("\n🎙️  Testing audio recognition...")
        
        # 尝试使用在线测试音频
        test_urls = [
            "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_example_zh.wav",
        ]
        
        # 首先尝试创建本地测试音频
        local_test_file = self.create_test_audio()
        
        for test_source in ([local_test_file] if local_test_file else []) + test_urls:
            if not test_source:
                continue
                
            print(f"  Testing with: {test_source}")
            start_time = time.time()
            
            try:
                if test_source.startswith("http"):
                    # 下载在线音频文件
                    audio_response = requests.get(test_source, timeout=30)
                    if audio_response.status_code != 200:
                        continue
                    audio_data = audio_response.content
                    filename = "downloaded_test.wav"
                    with open(filename, 'wb') as f:
                        f.write(audio_data)
                    test_file = filename
                else:
                    test_file = test_source
                
                if not os.path.exists(test_file):
                    continue
                
                # 发送识别请求
                with open(test_file, 'rb') as f:
                    files = {'audio': (test_file, f, 'audio/wav')}
                    response = requests.post(
                        f"{self.base_url}/api/recognize", 
                        files=files, 
                        timeout=60
                    )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        text = result.get("text", "")
                        sentences = result.get("sentences", [])
                        speakers = result.get("speakers", [])
                        
                        message = f"Text: '{text[:50]}...', Sentences: {len(sentences)}, Speakers: {len(speakers)}"
                        self.log_test("Audio Recognition", True, message, duration)
                        
                        # 清理临时文件
                        if test_file != test_source and os.path.exists(test_file):
                            os.remove(test_file)
                        
                        return True
                    else:
                        self.log_test("Audio Recognition", False, 
                                    f"Recognition failed: {result.get('message')}", duration)
                else:
                    self.log_test("Audio Recognition", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}", duration)
                
                # 清理临时文件
                if test_file != test_source and os.path.exists(test_file):
                    os.remove(test_file)
            
            except Exception as e:
                duration = time.time() - start_time
                self.log_test("Audio Recognition", False, 
                            f"Error: {e}", duration)
        
        # 清理本地测试文件
        if local_test_file and os.path.exists(local_test_file):
            os.remove(local_test_file)
        
        return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🚨 Testing error handling...")
        
        # 测试无效文件格式
        start_time = time.time()
        try:
            # 创建一个文本文件作为无效音频文件
            with open("invalid_audio.txt", "w") as f:
                f.write("This is not an audio file")
            
            with open("invalid_audio.txt", "rb") as f:
                files = {'audio': ('invalid_audio.txt', f, 'text/plain')}
                response = requests.post(
                    f"{self.base_url}/api/recognize", 
                    files=files, 
                    timeout=30
                )
            
            duration = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test("Error Handling (Invalid Format)", True, 
                            "Correctly rejected invalid file format", duration)
            else:
                self.log_test("Error Handling (Invalid Format)", False, 
                            f"Unexpected response: {response.status_code}", duration)
            
            # 清理
            os.remove("invalid_audio.txt")
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Error Handling (Invalid Format)", False, 
                        f"Error: {e}", duration)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 Starting AstroMao Test Suite")
        print("=" * 50)
        print(f"Target URL: {self.base_url}")
        
        # 运行测试
        tests = [
            self.test_server_health,
            self.test_web_interface,
            self.test_audio_recognition,
            self.test_error_handling,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 TEST REPORT")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # 保存详细报告
        report_file = "test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! AstroMao is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AstroMao Test Suite")
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost:8001", 
        help="Base URL of the AstroMao server"
    )
    parser.add_argument(
        "--wait", 
        type=int, 
        default=0, 
        help="Wait time (seconds) before starting tests"
    )
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds before starting tests...")
        time.sleep(args.wait)
    
    tester = AstroMaoTester(args.url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()