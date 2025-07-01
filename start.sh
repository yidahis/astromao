#!/bin/bash

# AstroMao 启动脚本

echo "=== AstroMao 语音识别系统 ==="
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import funasr, modelscope, fastapi" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查模型是否存在
if [ ! -d "models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch" ] || \
   [ ! -d "models/speech_fsmn_vad_zh-cn-16k-common-pytorch" ] || \
   [ ! -d "models/punc_ct-transformer_zh-cn-common-vocab272727-pytorch" ]; then
    echo "模型文件不完整，开始下载模型..."
    echo "注意: 首次下载需要较长时间，请耐心等待"
    python3 download_models.py
    
    if [ $? -ne 0 ]; then
        echo "模型下载失败，请检查网络连接后重试"
        exit 1
    fi
else
    echo "模型检查通过"
fi

echo
echo "启动 AstroMao 服务器..."
echo "服务器启动后，请访问: http://localhost:8001"
echo "按 Ctrl+C 停止服务器"
echo

# 启动应用
python3 app.py