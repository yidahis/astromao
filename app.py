#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import argparse
import logging
import os
import sys
import uuid
import json
import hashlib
import datetime
from typing import List, Dict, Any
import re

import aiofiles
import ffmpeg
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from modelscope.utils.logger import get_logger
from transformers import MarianMTModel, MarianTokenizer
import torch

from funasr import AutoModel

logger = get_logger(log_level=logging.INFO)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--host", type=str, default="0.0.0.0", required=False, help="host ip, localhost, 0.0.0.0"
)
parser.add_argument("--port", type=int, default=8001, required=False, help="server port")
parser.add_argument(
    "--asr_model",
    type=str,
    default="models/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    help="ASR model supporting Chinese and English with timestamp",
)
parser.add_argument(
    "--vad_model",
    type=str,
    default="models/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    help="VAD model for voice activity detection",
)
parser.add_argument(
    "--punc_model",
    type=str,
    default="models/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
    help="Punctuation model",
)
parser.add_argument(
    "--spk_model",
    type=str,
    default="models/speech_campplus_sv_zh-cn_16k-common",
    help="Speaker verification model",
)
parser.add_argument(
    "--sd_model",
    type=str,
    default="models/speech_diarization_sond-zh-cn-alimeeting-16k-n16k4-pytorch",
    help="Speaker diarization model",
)
parser.add_argument("--device", type=str, default="cpu", help="cuda, cpu")
parser.add_argument("--ncpu", type=int, default=4, help="cpu cores")
parser.add_argument("--temp_dir", type=str, default="temp_dir/", required=False, help="temp dir")
args = parser.parse_args()

logger.info("-----------  Configuration Arguments -----------")
for arg, value in vars(args).items():
    logger.info("%s: %s" % (arg, value))
logger.info("------------------------------------------------")

os.makedirs(args.temp_dir, exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("results", exist_ok=True)  # 创建结果存储目录

# 检查本地模型是否存在
def check_local_models():
    """检查本地模型文件是否存在"""
    models_to_check = [
        args.asr_model,
        args.vad_model,
        args.punc_model,
        args.spk_model,
        args.sd_model
    ]
    
    missing_models = []
    for model_path in models_to_check:
        if not os.path.exists(model_path):
            missing_models.append(model_path)
    
    if missing_models:
        logger.error("以下模型文件不存在:")
        for model in missing_models:
            logger.error(f"  - {model}")
        logger.error("请先运行 'python download_models.py' 下载模型")
        sys.exit(1)
    
    logger.info("本地模型检查通过")

check_local_models()
logger.info("Loading models...")
# Load FunASR models
try:
    # ASR model with speaker diarization
    model = AutoModel(
        model=args.asr_model,
        vad_model=args.vad_model,
        punc_model=args.punc_model,
        spk_model=args.spk_model,
        device=args.device,
        ncpu=args.ncpu,
        disable_pbar=True,
        disable_log=True,
        disable_update=True,
    )
    logger.info("Models loaded successfully!")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    # Fallback to basic model without speaker features
    model = AutoModel(
        model=args.asr_model,
        vad_model=args.vad_model,
        punc_model=args.punc_model,
        device=args.device,
        ncpu=args.ncpu,
        disable_pbar=True,
        disable_log=True,
        disable_update=True,
    )
    logger.info("Basic models loaded (without speaker features)!")

# Initialize local translation models
class LocalTranslator:
    def __init__(self):
        self.zh_to_en_model = None
        self.zh_to_en_tokenizer = None
        self.en_to_zh_model = None
        self.en_to_zh_tokenizer = None
        self.load_models()
    
    def load_models(self):
        """加载本地翻译模型"""
        try:
            # 中文到英文模型
            zh_en_model_name = "Helsinki-NLP/opus-mt-zh-en"
            self.zh_to_en_tokenizer = MarianTokenizer.from_pretrained(zh_en_model_name)
            self.zh_to_en_model = MarianMTModel.from_pretrained(zh_en_model_name)
            
            # 英文到中文模型
            en_zh_model_name = "Helsinki-NLP/opus-mt-en-zh"
            self.en_to_zh_tokenizer = MarianTokenizer.from_pretrained(en_zh_model_name)
            self.en_to_zh_model = MarianMTModel.from_pretrained(en_zh_model_name)
            
            logger.info("Local translation models loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load translation models: {e}")
            logger.warning("Translation functionality will be disabled")
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """执行翻译"""
        if not text.strip():
            return text
        
        try:
            if source_lang == 'zh' and target_lang == 'en':
                if self.zh_to_en_model is None:
                    return text
                tokenizer = self.zh_to_en_tokenizer
                model = self.zh_to_en_model
            elif source_lang == 'en' and target_lang == 'zh':
                if self.en_to_zh_model is None:
                    return text
                tokenizer = self.en_to_zh_tokenizer
                model = self.en_to_zh_model
            else:
                return text
            
            # 编码输入文本
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # 生成翻译
            with torch.no_grad():
                outputs = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
            
            # 解码输出
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return translated
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text

# 初始化翻译器
translator = LocalTranslator()

# Translation functions
def detect_language(text: str) -> str:
    """检测文本语言"""
    try:
        # 简单的中文检测
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if len(chinese_chars) > len(text) * 0.3:  # 如果中文字符超过30%
            return 'zh'
        else:
            return 'en'
    except:
        return 'auto'

def translate_text(text: str, target_lang: str = None) -> Dict[str, str]:
    """翻译文本"""
    if not text.strip():
        return {"original": text, "translated": text, "source_lang": "unknown", "target_lang": target_lang or "unknown"}
    
    try:
        # 检测源语言
        source_lang = detect_language(text)
        
        # 如果没有指定目标语言，自动选择
        if not target_lang:
            target_lang = 'en' if source_lang == 'zh' else 'zh'
        
        # 如果源语言和目标语言相同，不需要翻译
        if source_lang == target_lang:
            return {"original": text, "translated": text, "source_lang": source_lang, "target_lang": target_lang}
        
        # 执行翻译
        translated_text = translator.translate(text, source_lang, target_lang)
        
        return {
            "original": text,
            "translated": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return {"original": text, "translated": text, "source_lang": "unknown", "target_lang": target_lang or "unknown"}

app = FastAPI(title="AstroMao - 离线语音识别Web应用")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    return FileResponse("static/index.html")


@app.post("/api/recognize")
async def recognize_audio(audio: UploadFile = File(..., description="Audio file for recognition")):
    """音频识别API"""
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Check file format
    allowed_formats = ["wav", "mp3", "m4a", "flac", "aac", "ogg"]
    suffix = audio.filename.split(".")[-1].lower()
    if suffix not in allowed_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {', '.join(allowed_formats)}"
        )
    
    # Save uploaded file
    audio_path = f"{args.temp_dir}/{str(uuid.uuid1())}.{suffix}"
    try:
        async with aiofiles.open(audio_path, "wb") as out_file:
            content = await audio.read()
            await out_file.write(content)
    except Exception as e:
        logger.error(f"Failed to save audio file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save audio file")
    
    try:
        # Calculate audio file hash
        with open(audio_path, 'rb') as f:
            audio_hash = hashlib.md5(f.read()).hexdigest()
        
        # Convert audio to required format
        audio_bytes, _ = (
            ffmpeg.input(audio_path, threads=0)
            .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except Exception as e:
        logger.error(f"Failed to process audio file: {e}")
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(status_code=500, detail="Failed to process audio file")
    
    try:
        # Perform recognition
        param_dict = {
            "batch_size_s": 300,
            "merge_vad": True,
            "merge_length_s": 15,
        }
        
        # Add timestamp parameter only if model supports it
        try:
            param_dict["sentence_timestamp"] = True
            rec_results = model.generate(input=audio_bytes, is_final=True, **param_dict)
        except Exception as timestamp_error:
            logger.warning(f"Timestamp not supported, falling back: {timestamp_error}")
            # Retry without timestamp
            param_dict.pop("sentence_timestamp", None)
            rec_results = model.generate(input=audio_bytes, is_final=True, **param_dict)
        
        # Clean up temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Process results
        if len(rec_results) == 0:
            return {
                "success": True,
                "text": "",
                "sentences": [],
                "speakers": [],
                "message": "No speech detected"
            }
        
        result = rec_results[0]
        text = result.get("text", "")
        sentences = []
        speakers = set()
        
        # Process sentence information
        sentence_info = result.get("sentence_info", [])
        if sentence_info:
            # Model supports detailed sentence info
            for i, sentence in enumerate(sentence_info):
                sentence_text = sentence.get("text", "")
                start_time = sentence.get("start", 0) / 1000  # Convert to seconds
                end_time = sentence.get("end", 0) / 1000
                
                # Extract speaker information if available
                speaker_id = sentence.get("spk", f"Speaker_{i % 2 + 1}")
                speakers.add(speaker_id)
                
                # 翻译句子
                translation_zh = translate_text(sentence_text, 'zh')
                translation_en = translate_text(sentence_text, 'en')
                
                sentences.append({
                    "text": sentence_text,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "speaker": speaker_id,
                    "translation": {
                        "zh": translation_zh["translated"],
                        "en": translation_en["translated"],
                        "source_lang": translation_zh["source_lang"]
                    }
                })
        else:
            # Fallback: create single sentence from full text
            translation_zh = translate_text(text, 'zh')
            translation_en = translate_text(text, 'en')
            
            sentences.append({
                "text": text,
                "start": 0.0,
                "end": 0.0,
                "speaker": "Speaker_1",
                "translation": {
                    "zh": translation_zh["translated"],
                    "en": translation_en["translated"],
                    "source_lang": translation_zh["source_lang"]
                }
            })
            speakers.add("Speaker_1")
        
        # Generate unique result ID
        result_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        response = {
            "success": True,
            "result_id": result_id,
            "text": text,
            "sentences": sentences,
            "speakers": list(speakers),
            "total_duration": round(max([s["end"] for s in sentences], default=0), 2),
            "audio_hash": audio_hash,
            "filename": audio.filename,
            "timestamp": timestamp,
            "message": "Recognition completed successfully"
        }
        
        logger.info(f"Recognition result: {len(sentences)} sentences, {len(speakers)} speakers")
        return response
        
    except Exception as e:
        logger.error(f"Recognition failed: {e}")
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查API"""
    return {
        "status": "healthy",
        "models_loaded": True,
        "supported_formats": ["wav", "mp3", "m4a", "flac", "aac", "ogg"]
    }


@app.post("/api/save_result")
async def save_result(result_data: dict):
    """保存识别结果到本地文件"""
    try:
        result_id = result_data.get("result_id")
        if not result_id:
            raise HTTPException(status_code=400, detail="Missing result_id")
        
        # 保存结果到JSON文件
        result_file = f"results/{result_id}.json"
        async with aiofiles.open(result_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(result_data, ensure_ascii=False, indent=2))
        
        logger.info(f"Result saved: {result_file}")
        return {
            "success": True,
            "result_id": result_id,
            "file_path": result_file,
            "message": "Result saved successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to save result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save result: {str(e)}")


@app.get("/api/export/{result_id}")
async def export_result(result_id: str):
    """导出指定ID的识别结果为JSON文件"""
    try:
        result_file = f"results/{result_id}.json"
        if not os.path.exists(result_file):
            raise HTTPException(status_code=404, detail="Result not found")
        
        return FileResponse(
            path=result_file,
            filename=f"astromao_result_{result_id}.json",
            media_type="application/json"
        )
    
    except Exception as e:
        logger.error(f"Failed to export result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export result: {str(e)}")


@app.get("/api/results")
async def list_results():
    """列出所有保存的识别结果"""
    try:
        results = []
        results_dir = "results"
        
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if filename.endswith('.json'):
                    result_id = filename[:-5]  # 移除.json后缀
                    file_path = os.path.join(results_dir, filename)
                    
                    # 读取文件基本信息
                    stat = os.stat(file_path)
                    created_time = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
                    file_size = stat.st_size
                    
                    # 尝试读取文件内容获取更多信息
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            data = json.loads(content)
                            
                            results.append({
                                "result_id": result_id,
                                "filename": data.get("filename", "unknown"),
                                "original_filename": data.get("filename", "unknown"),  # 原始音频文件名
                                "audio_hash": data.get("audio_hash", ""),
                                "text_preview": data.get("text", "")[:100] + "..." if len(data.get("text", "")) > 100 else data.get("text", ""),
                                "speakers_count": len(data.get("speakers", [])),
                                "sentences_count": len(data.get("sentences", [])),
                                "total_duration": data.get("total_duration", 0),
                                "timestamp": data.get("timestamp", created_time),
                                "file_size": file_size
                            })
                    except Exception as e:
                        logger.warning(f"Failed to read result file {filename}: {e}")
                        results.append({
                            "result_id": result_id,
                            "filename": "unknown",
                            "created_time": created_time,
                            "file_size": file_size,
                            "error": "Failed to read file content"
                        })
        
        # 按时间戳排序（最新的在前）
        results.sort(key=lambda x: x.get("timestamp", x.get("created_time", "")), reverse=True)
        
        return {
            "success": True,
            "results": results,
            "total_count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Failed to list results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list results: {str(e)}")


@app.post("/api/upload_audio/{result_id}")
async def upload_audio_for_result(result_id: str, audio: UploadFile = File(...)):
    """为指定结果上传并保存音频文件"""
    logger.info(f"收到音频上传请求 - result_id: {result_id}, filename: {audio.filename}")
    try:
        # 确保results目录存在
        os.makedirs("results", exist_ok=True)
        logger.info(f"确保results目录存在")
        
        # 生成音频文件名（保持原始扩展名）
        file_extension = os.path.splitext(audio.filename)[1] if audio.filename else '.wav'
        audio_filename = f"{result_id}_audio{file_extension}"
        audio_path = f"results/{audio_filename}"
        logger.info(f"生成音频文件路径: {audio_path}")
        
        # 保存音频文件
        logger.info(f"开始保存音频文件...")
        async with aiofiles.open(audio_path, 'wb') as f:
            content = await audio.read()
            await f.write(content)
            logger.info(f"音频文件内容已写入，大小: {len(content)} bytes")
        
        # 验证文件是否成功保存
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logger.info(f"音频文件保存成功: {audio_path}, 文件大小: {file_size} bytes")
        else:
            logger.error(f"音频文件保存失败: 文件不存在 {audio_path}")
            raise Exception("文件保存失败")
        
        return {
            "success": True,
            "audio_path": audio_filename,  # 返回相对路径
            "message": "Audio file uploaded successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to upload audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {str(e)}")


@app.get("/api/audio/{audio_filename}")
async def get_audio_file(audio_filename: str):
    """获取保存的音频文件"""
    try:
        audio_path = f"results/{audio_filename}"
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=audio_path,
            filename=audio_filename,
            media_type="audio/mpeg"  # 通用音频类型
        )
    
    except Exception as e:
        logger.error(f"Failed to get audio file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio file: {str(e)}")


@app.put("/api/update_result/{result_id}")
async def update_result(result_id: str, result_data: dict):
    """更新已保存的识别结果"""
    try:
        result_file = f"results/{result_id}.json"
        
        # 确保结果目录存在
        os.makedirs("results", exist_ok=True)
        
        # 更新时间戳
        result_data["updated_timestamp"] = datetime.datetime.now().isoformat()
        
        # 保存更新后的结果
        async with aiofiles.open(result_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(result_data, ensure_ascii=False, indent=2))
        
        logger.info(f"Result updated: {result_file}")
        return {
            "success": True,
            "result_id": result_id,
            "message": "Result updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to update result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update result: {str(e)}")


@app.delete("/api/results/{result_id}")
async def delete_result(result_id: str):
    """删除指定ID的识别结果"""
    try:
        result_file = f"results/{result_id}.json"
        if not os.path.exists(result_file):
            raise HTTPException(status_code=404, detail="Result not found")
        
        # 删除JSON文件
        os.remove(result_file)
        logger.info(f"Result JSON deleted: {result_file}")
        
        # 查找并删除对应的音频文件
        audio_files_deleted = []
        for ext in ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg']:
            audio_file = f"results/{result_id}_audio{ext}"
            if os.path.exists(audio_file):
                os.remove(audio_file)
                audio_files_deleted.append(audio_file)
                logger.info(f"Audio file deleted: {audio_file}")
        
        message = "Result deleted successfully"
        if audio_files_deleted:
            message += f", audio files deleted: {', '.join(audio_files_deleted)}"
        
        return {
            "success": True,
            "result_id": result_id,
            "message": message,
            "deleted_files": [result_file] + audio_files_deleted
        }
    
    except Exception as e:
        logger.error(f"Failed to delete result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host=args.host, port=args.port)