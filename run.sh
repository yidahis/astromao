#!/bin/bash

# AstroMao 语音识别Web应用启动脚本

echo "🚀 Starting AstroMao Speech Recognition Web App..."
echo "================================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# 检查ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg is not installed. Installing ffmpeg..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "❌ Please install Homebrew first, then run: brew install ffmpeg"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo "❌ Please install ffmpeg manually for your operating system"
        exit 1
    fi
fi

# 创建虚拟环境（可选）
if [ "$1" = "--venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv astromao_env
    source astromao_env/bin/activate
    echo "✅ Virtual environment activated"
fi

# 安装依赖
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# 创建必要的目录
mkdir -p temp_dir
mkdir -p static

# 设置默认参数
HOST=${HOST:-"localhost"}
PORT=${PORT:-8001}
DEVICE=${DEVICE:-"cpu"}

echo "🔧 Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Device: $DEVICE"
echo ""

# 启动应用
echo "🎙️  Starting AstroMao Web App..."
echo "📱 Open your browser and visit: http://localhost:$PORT"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

python3 app.py --host $HOST --port $PORT --device $DEVICE