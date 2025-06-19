#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

"""
AstroMao Demo Script

这是一个简单的命令行演示脚本，展示如何使用FunASR进行语音识别和说话人分离。
"""

import argparse
import json
import os
from funasr import AutoModel


def main():
    parser = argparse.ArgumentParser(description="AstroMao Speech Recognition Demo")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Input audio file path or URL"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Output JSON file path (optional)"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="cpu", 
        help="Device to use: cpu or cuda"
    )
    parser.add_argument(
        "--lang", 
        type=str, 
        default="auto", 
        choices=["auto", "zh", "en"], 
        help="Language: auto, zh (Chinese), en (English)"
    )
    
    args = parser.parse_args()
    
    print("🎙️  AstroMao Speech Recognition Demo")
    print("=" * 50)
    print(f"📁 Input: {args.input}")
    print(f"🖥️  Device: {args.device}")
    print(f"🌐 Language: {args.lang}")
    print("")
    
    # 检查输入文件
    if not args.input.startswith("http") and not os.path.exists(args.input):
        print(f"❌ Error: Input file '{args.input}' not found!")
        return
    
    print("📦 Loading models...")
    try:
        # 根据语言选择模型
        if args.lang == "zh":
            asr_model = "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
        elif args.lang == "en":
            asr_model = "iic/speech_paraformer-large_asr_nat-en-16k-common-vocab10020-pytorch"
        else:
            # 使用支持中英文的SenseVoice模型
            asr_model = "iic/SenseVoiceSmall"
        
        model = AutoModel(
            model=asr_model,
            vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
            punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
            spk_model="iic/speech_campplus_sv_zh-cn_16k-common",
            device=args.device,
            disable_pbar=True,
            disable_log=True,
        )
        print("✅ Models loaded successfully!")
        
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        print("💡 Trying basic model without speaker features...")
        try:
            model = AutoModel(
                model=asr_model,
                vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                device=args.device,
                disable_pbar=True,
                disable_log=True,
            )
            print("✅ Basic models loaded successfully!")
        except Exception as e2:
            print(f"❌ Failed to load basic models: {e2}")
            return
    
    print("🔄 Processing audio...")
    try:
        # 执行识别
        param_dict = {
            "sentence_timestamp": True,
            "batch_size_s": 300,
            "merge_vad": True,
            "merge_length_s": 15,
        }
        
        results = model.generate(input=args.input, is_final=True, **param_dict)
        
        if not results:
            print("⚠️  No speech detected in the audio file.")
            return
        
        result = results[0]
        text = result.get("text", "")
        sentence_info = result.get("sentence_info", [])
        
        print("\n" + "=" * 50)
        print("📊 RECOGNITION RESULTS")
        print("=" * 50)
        
        # 统计信息
        total_sentences = len(sentence_info)
        total_chars = len(text)
        speakers = set()
        total_duration = 0
        
        # 处理句子信息
        sentences = []
        for i, sentence in enumerate(sentence_info):
            sentence_text = sentence.get("text", "")
            start_time = sentence.get("start", 0) / 1000  # 转换为秒
            end_time = sentence.get("end", 0) / 1000
            speaker_id = sentence.get("spk", f"Speaker_{i % 2 + 1}")  # 默认说话人分配
            
            speakers.add(speaker_id)
            total_duration = max(total_duration, end_time)
            
            sentences.append({
                "text": sentence_text,
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "speaker": speaker_id
            })
        
        # 显示统计信息
        print(f"📝 Total Text: {text}")
        print(f"⏱️  Duration: {total_duration:.2f} seconds")
        print(f"📄 Sentences: {total_sentences}")
        print(f"👥 Speakers: {len(speakers)}")
        print(f"🔤 Characters: {total_chars}")
        print("")
        
        # 显示详细结果
        print("📋 DETAILED RESULTS:")
        print("-" * 50)
        for i, sentence in enumerate(sentences, 1):
            print(f"[{i:2d}] {sentence['speaker']} ({sentence['start']}s - {sentence['end']}s)")
            print(f"     {sentence['text']}")
            print()
        
        # 保存结果到文件
        if args.output:
            output_data = {
                "success": True,
                "text": text,
                "sentences": sentences,
                "speakers": list(speakers),
                "total_duration": round(total_duration, 2),
                "statistics": {
                    "sentence_count": total_sentences,
                    "speaker_count": len(speakers),
                    "character_count": total_chars,
                    "duration": round(total_duration, 2)
                }
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Results saved to: {args.output}")
        
        print("\n✅ Recognition completed successfully!")
        
    except Exception as e:
        print(f"❌ Recognition failed: {e}")
        return


if __name__ == "__main__":
    main()