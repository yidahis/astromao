#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroMao - 性能测试脚本
用于测试语音识别服务的性能和准确性
"""

import os
import sys
import time
import json
import argparse
import asyncio
import aiohttp
import statistics
from pathlib import Path
from typing import List, Dict, Any

class AstroMaoBenchmark:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.results = []
        
    async def test_single_file(self, session: aiohttp.ClientSession, 
                              file_path: str, test_id: int) -> Dict[str, Any]:
        """
        测试单个音频文件的识别性能
        """
        start_time = time.time()
        
        try:
            # 准备文件上传
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('audio', f, filename=os.path.basename(file_path))
                
                # 发送请求
                request_start = time.time()
                async with session.post(f"{self.server_url}/api/recognize", 
                                       data=data) as response:
                    request_end = time.time()
                    
                    if response.status == 200:
                        result = await response.json()
                        total_time = time.time() - start_time
                        
                        # 计算性能指标
                        file_size = os.path.getsize(file_path)
                        audio_duration = result.get('duration', 0)
                        processing_time = result.get('processing_time', request_end - request_start)
                        
                        return {
                            'test_id': test_id,
                            'file_path': file_path,
                            'file_size': file_size,
                            'audio_duration': audio_duration,
                            'processing_time': processing_time,
                            'total_time': total_time,
                            'request_time': request_end - request_start,
                            'rtf': processing_time / audio_duration if audio_duration > 0 else 0,
                            'throughput': file_size / total_time,
                            'success': True,
                            'result': result
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'test_id': test_id,
                            'file_path': file_path,
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}",
                            'total_time': time.time() - start_time
                        }
                        
        except Exception as e:
            return {
                'test_id': test_id,
                'file_path': file_path,
                'success': False,
                'error': str(e),
                'total_time': time.time() - start_time
            }
    
    async def run_concurrent_tests(self, file_paths: List[str], 
                                 concurrent_requests: int = 1) -> List[Dict[str, Any]]:
        """
        运行并发测试
        """
        async with aiohttp.ClientSession() as session:
            # 创建测试任务
            tasks = []
            for i, file_path in enumerate(file_paths):
                for j in range(concurrent_requests):
                    test_id = i * concurrent_requests + j
                    task = self.test_single_file(session, file_path, test_id)
                    tasks.append(task)
            
            # 执行所有测试
            print(f"开始执行 {len(tasks)} 个测试任务...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'test_id': i,
                        'success': False,
                        'error': str(result),
                        'total_time': 0
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析测试结果
        """
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]
        
        if not successful_results:
            return {
                'total_tests': len(results),
                'successful_tests': 0,
                'failed_tests': len(failed_results),
                'success_rate': 0.0,
                'errors': [r.get('error', 'Unknown error') for r in failed_results]
            }
        
        # 计算性能统计
        processing_times = [r['processing_time'] for r in successful_results if 'processing_time' in r]
        total_times = [r['total_time'] for r in successful_results]
        rtfs = [r['rtf'] for r in successful_results if 'rtf' in r and r['rtf'] > 0]
        throughputs = [r['throughput'] for r in successful_results if 'throughput' in r]
        
        analysis = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'failed_tests': len(failed_results),
            'success_rate': len(successful_results) / len(results) * 100,
            'performance': {
                'processing_time': {
                    'mean': statistics.mean(processing_times) if processing_times else 0,
                    'median': statistics.median(processing_times) if processing_times else 0,
                    'min': min(processing_times) if processing_times else 0,
                    'max': max(processing_times) if processing_times else 0,
                    'std': statistics.stdev(processing_times) if len(processing_times) > 1 else 0
                },
                'total_time': {
                    'mean': statistics.mean(total_times) if total_times else 0,
                    'median': statistics.median(total_times) if total_times else 0,
                    'min': min(total_times) if total_times else 0,
                    'max': max(total_times) if total_times else 0
                },
                'rtf': {
                    'mean': statistics.mean(rtfs) if rtfs else 0,
                    'median': statistics.median(rtfs) if rtfs else 0,
                    'min': min(rtfs) if rtfs else 0,
                    'max': max(rtfs) if rtfs else 0
                },
                'throughput_mbps': {
                    'mean': statistics.mean(throughputs) / 1024 / 1024 if throughputs else 0,
                    'median': statistics.median(throughputs) / 1024 / 1024 if throughputs else 0
                }
            }
        }
        
        if failed_results:
            analysis['errors'] = [r.get('error', 'Unknown error') for r in failed_results]
        
        return analysis
    
    def print_results(self, analysis: Dict[str, Any]):
        """
        打印测试结果
        """
        print("\n" + "="*60)
        print("AstroMao 性能测试报告")
        print("="*60)
        
        print(f"\n📊 测试概览:")
        print(f"  总测试数: {analysis['total_tests']}")
        print(f"  成功测试: {analysis['successful_tests']}")
        print(f"  失败测试: {analysis['failed_tests']}")
        print(f"  成功率: {analysis['success_rate']:.1f}%")
        
        if analysis['successful_tests'] > 0:
            perf = analysis['performance']
            print(f"\n⚡ 性能指标:")
            print(f"  处理时间 (秒):")
            print(f"    平均: {perf['processing_time']['mean']:.3f}")
            print(f"    中位数: {perf['processing_time']['median']:.3f}")
            print(f"    最小: {perf['processing_time']['min']:.3f}")
            print(f"    最大: {perf['processing_time']['max']:.3f}")
            
            print(f"  实时因子 (RTF):")
            print(f"    平均: {perf['rtf']['mean']:.3f}")
            print(f"    中位数: {perf['rtf']['median']:.3f}")
            print(f"    最小: {perf['rtf']['min']:.3f}")
            print(f"    最大: {perf['rtf']['max']:.3f}")
            
            print(f"  吞吐量:")
            print(f"    平均: {perf['throughput_mbps']['mean']:.2f} MB/s")
            print(f"    中位数: {perf['throughput_mbps']['median']:.2f} MB/s")
        
        if 'errors' in analysis:
            print(f"\n❌ 错误信息:")
            for error in set(analysis['errors']):
                count = analysis['errors'].count(error)
                print(f"  {error} (出现 {count} 次)")
        
        print("\n" + "="*60)

async def main():
    parser = argparse.ArgumentParser(description="AstroMao 性能测试")
    parser.add_argument("--server", "-s", default="http://localhost:8000", 
                       help="服务器URL")
    parser.add_argument("--files", "-f", nargs="+", 
                       help="测试音频文件路径")
    parser.add_argument("--directory", "-d", 
                       help="测试音频文件目录")
    parser.add_argument("--concurrent", "-c", type=int, default=1,
                       help="并发请求数")
    parser.add_argument("--output", "-o", 
                       help="结果输出文件 (JSON格式)")
    parser.add_argument("--generate-test-audio", action="store_true",
                       help="生成测试音频文件")
    
    args = parser.parse_args()
    
    # 生成测试音频
    if args.generate_test_audio:
        print("生成测试音频文件...")
        os.system("python sample_audio.py -o test_short.wav -d 3")
        os.system("python sample_audio.py -o test_long.wav -d 10")
        os.system("python sample_audio.py --multi-speaker -o test_multi.wav -d 8")
        print("测试音频文件已生成")
    
    # 确定测试文件
    test_files = []
    if args.files:
        test_files.extend(args.files)
    elif args.directory:
        audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac']
        for ext in audio_extensions:
            test_files.extend(Path(args.directory).glob(f"*{ext}"))
        test_files = [str(f) for f in test_files]
    else:
        # 使用默认测试文件
        default_files = ['test_short.wav', 'test_long.wav', 'test_multi.wav']
        test_files = [f for f in default_files if os.path.exists(f)]
        
        if not test_files:
            print("未找到测试文件，请使用 --generate-test-audio 生成测试音频")
            return
    
    if not test_files:
        print("未找到可用的测试文件")
        return
    
    print(f"找到 {len(test_files)} 个测试文件")
    for f in test_files:
        print(f"  - {f}")
    
    # 运行测试
    benchmark = AstroMaoBenchmark(args.server)
    
    print(f"\n开始性能测试 (并发数: {args.concurrent})...")
    start_time = time.time()
    
    results = await benchmark.run_concurrent_tests(test_files, args.concurrent)
    
    end_time = time.time()
    print(f"测试完成，总耗时: {end_time - start_time:.2f} 秒")
    
    # 分析结果
    analysis = benchmark.analyze_results(results)
    benchmark.print_results(analysis)
    
    # 保存结果
    if args.output:
        output_data = {
            'timestamp': time.time(),
            'test_duration': end_time - start_time,
            'configuration': {
                'server_url': args.server,
                'concurrent_requests': args.concurrent,
                'test_files': test_files
            },
            'analysis': analysis,
            'raw_results': results
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n详细结果已保存到: {args.output}")

if __name__ == "__main__":
    asyncio.run(main())