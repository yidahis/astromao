#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型下载脚本
从ModelScope下载所需的模型到本地models文件夹
"""

import os
import sys
from pathlib import Path

def download_models():
    """下载所需的模型到models文件夹"""
    
    # 确保models文件夹存在
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    try:
        from modelscope import snapshot_download
        print("正在下载模型...")
        
        # 下载支持时间戳的ASR模型
        asr_model_path = models_dir / "speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
        if not asr_model_path.exists():
            print("下载语音识别模型（支持时间戳）...")
            snapshot_download(
                "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                cache_dir=str(models_dir),
                local_dir=str(asr_model_path)
            )
            print("语音识别模型下载完成")
        else:
            print("语音识别模型已存在，跳过下载")
        
        # 下载VAD模型
        vad_model_path = models_dir / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
        if not vad_model_path.exists():
            print("下载VAD模型...")
            snapshot_download(
                "damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                cache_dir=str(models_dir),
                local_dir=str(vad_model_path)
            )
            print("VAD模型下载完成")
        else:
            print("VAD模型已存在，跳过下载")
        
        # 下载标点符号模型
        punc_model_path = models_dir / "punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
        if not punc_model_path.exists():
            print("下载标点符号模型...")
            snapshot_download(
                "damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                cache_dir=str(models_dir),
                local_dir=str(punc_model_path)
            )
            print("标点符号模型下载完成")
        else:
            print("标点符号模型已存在，跳过下载")
        
        # 下载说话人识别模型
        spk_model_path = models_dir / "speech_campplus_sv_zh-cn_16k-common"
        if not spk_model_path.exists():
            print("下载说话人识别模型...")
            snapshot_download(
                "iic/speech_campplus_sv_zh-cn_16k-common",
                cache_dir=str(models_dir),
                local_dir=str(spk_model_path)
            )
            print("说话人识别模型下载完成")
        else:
            print("说话人识别模型已存在，跳过下载")
        
        # 下载语音分离模型
        diarization_model_path = models_dir / "speech_diarization_sond-zh-cn-alimeeting-16k-n16k4-pytorch"
        if not diarization_model_path.exists():
            print("下载语音分离模型...")
            snapshot_download(
                "iic/speech_diarization_sond-zh-cn-alimeeting-16k-n16k4-pytorch",
                cache_dir=str(models_dir),
                local_dir=str(diarization_model_path)
            )
            print("语音分离模型下载完成")
        else:
            print("语音分离模型已存在，跳过下载")
        
        print("所有模型下载完成！")
        
    except ImportError:
        print("错误：未安装modelscope库")
        print("请运行：pip install modelscope")
        sys.exit(1)
    except Exception as e:
        print(f"下载模型时出错：{e}")
        sys.exit(1)

if __name__ == "__main__":
    download_models()