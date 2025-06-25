# AstroMao - 离线语音识别Web应用

![AstroMao 语音识别应用](https://raw.githubusercontent.com/yidahis/astromao/refs/heads/master/static/main.png)

这是一个基于FunASR的离线语音识别Web应用，支持说话人分离、中英文识别和音频文件上传。

## ✨ 功能特性

- 🎯 **离线语音识别**: 基于FunASR的高精度中英文语音识别
- 👥 **说话人分离**: 自动识别和区分不同说话人
- 🌐 **Web界面**: 现代化的响应式Web界面
- 📁 **多格式支持**: 支持WAV、MP3、M4A、FLAC、AAC、OGG等音频格式
- ⚡ **实时处理**: 快速音频处理和识别
- 📊 **详细结果**: 提供时间戳、说话人标签和完整转录文本
- 🎵 **音频播放**: 点击分句直接播放对应时间段的音频
- 📥 **结果导入**: 支持导入之前保存的JSON识别结果文件，并可验证对应音频文件
- 💾 **结果保存**: 自动保存识别结果，包含音频文件hash值
- 📥 **结果导出**: 支持导出JSON格式的识别结果
- 📋 **历史记录**: 查看、管理和导出历史识别结果
- 🔧 **易于部署**: 支持Docker容器化部署
- 🎨 **美观界面**: 现代化UI设计，支持拖拽上传

## 技术栈

- **后端**: FastAPI + FunASR
- **前端**: HTML + CSS + JavaScript
- **模型**: 
  - ASR: SenseVoice (支持中英文)
  - VAD: FSMN-VAD (语音活动检测)
  - 标点: CT-Transformer (标点恢复)
  - 说话人分离: CAM++ (说话人分离)

## 安装依赖

```bash
pip install funasr fastapi uvicorn aiofiles ffmpeg-python
```

## 使用方法

1. 启动服务:
```bash
python app.py
```

2. 打开浏览器访问: http://localhost:8001

3. 上传音频文件进行识别

## 📖 使用说明

### 基本使用流程

1. **上传音频文件**
   - 支持拖拽上传或点击选择文件
   - 支持多种音频格式（WAV、MP3、M4A、FLAC、AAC、OGG）

2. **开始识别**
   - 点击"开始识别"按钮
   - 等待处理完成，可查看实时进度

3. **查看结果**
   - 查看完整转录文本
   - 查看分句结果和说话人信息
   - 查看统计信息（时长、句子数、说话人数、字符数）
   - 点击任意分句可播放对应时间段的音频

4. **导入结果**
   - 点击"📥 导入JSON结果"按钮可以导入之前保存的识别结果文件
   - 如果需要播放音频，点击"选择对应音频"按钮
   - 系统会验证音频文件的hash值确保一致性

### 结果管理功能

4. **保存结果**
   - 点击"💾 保存结果"按钮保存当前识别结果
   - 系统自动生成唯一ID和计算音频文件hash值

5. **导出结果**
   - 点击"📥 导出JSON"按钮下载结果文件
   - 导出的JSON文件包含完整的识别信息和元数据

6. **历史记录管理**
   - 点击"📋 历史记录"查看所有保存的识别结果
   - 支持查看结果预览、导出和删除操作
   - 历史记录按时间排序，显示文件信息和识别统计

## 项目结构

```
astromao/
├── README.md              # 项目说明文档
├── requirements.txt       # Python依赖
├── config.yaml           # 配置文件
├── app.py                # Web应用主程序
├── demo.py               # 命令行测试脚本科技你要 ·1且34567890-=【】=-098764の为去 ··1234

├── test.py               # 自动化测试脚本
├── benchmark.py          # 性能测试脚本
├── sample_audio.py       # 示例音频生成器
├── run.sh                # 启动脚本
├── Dockerfile            # Docker镜像构建文件
├── docker-compose.yml    # Docker Compose配置
├── .gitignore            # Git忽略文件
├── results/              # 识别结果存储目录
│   └── *.json           # 保存的识别结果文件
└── static/
    └── index.html        # Web前端页面
```

## 支持的音频格式

- WAV (推荐)
- MP3
- M4A
- FLAC
- AAC
- OGG

## 📡 API 接口

### 音频识别
```bash
POST /api/recognize
# 上传音频文件进行识别
# 返回包含result_id、audio_hash等信息的识别结果
```

### 保存识别结果
```bash
POST /api/save_result
# 保存识别结果到本地JSON文件
# Body: 识别结果JSON数据
```

### 导出识别结果
```bash
GET /api/export/{result_id}
# 下载指定ID的识别结果JSON文件
```

### 获取历史记录
```bash
GET /api/results
# 获取所有保存的识别结果列表
```

### 删除识别结果
```bash
DELETE /api/results/{result_id}
# 删除指定ID的识别结果
```

### 健康检查
```bash
GET /api/health
# 检查服务状态
```

## 输出格式

识别结果以JSON格式返回：

```json
{
  "success": true,
  "result_id": "uuid-string",
  "text": "完整的识别文本",
  "sentences": [
    {
      "text": "句子文本",
      "start": 0.0,
      "end": 2.5,
      "speaker": "Speaker_1"
    }
  ],
  "speakers": ["Speaker_1", "Speaker_2"],
  "total_duration": 10.5,
  "audio_hash": "md5-hash-value",
  "filename": "original-filename.wav",
  "timestamp": "2024-01-01T12:00:00.000000",
  "message": "Recognition completed successfully"
}
```

## 高级功能

### 1. 命令行测试

```bash
# 测试单个音频文件
python demo.py input.wav

# 指定输出文件和语言
python demo.py input.wav --output result.json --language zh

# 使用GPU加速
python demo.py input.wav --device cuda
```

### 2. 生成测试音频

```bash
# 生成简单测试音频
python sample_audio.py --output test.wav --duration 5

# 生成多说话人音频
python sample_audio.py --multi-speaker --output multi_test.wav

# 下载真实示例音频
python sample_audio.py --download
```

### 3. 性能测试

```bash
# 生成测试音频并运行基准测试
python benchmark.py --generate-test-audio

# 测试指定文件
python benchmark.py --files test1.wav test2.wav

# 并发测试
python benchmark.py --concurrent 4 --output benchmark_result.json

# 测试目录中的所有音频
python benchmark.py --directory ./audio_samples/
```

### 4. 自动化测试

```bash
# 运行完整测试套件
python test.py

# 指定服务器地址
python test.py --server http://localhost:8001

# 测试前等待服务启动
python test.py --wait 10
```

## Docker部署

### 方式1：使用Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式2：使用Docker

```bash
# 构建镜像
docker build -t astromao .

# 运行容器
docker run -p 8001:8001 astromao

# 挂载数据卷
docker run -p 8001:8001 -v $(pwd)/temp_dir:/app/temp_dir astromao
```

### 方式3：使用Nginx反向代理

```bash
# 启动包含Nginx的完整服务
docker-compose --profile with-nginx up
```

## 配置说明

主要配置项在 `config.yaml` 中：

- **服务器设置**：主机、端口、临时目录
- **设备配置**：CPU/GPU、核心数
- **模型配置**：ASR、VAD、PUNC、Speaker、Diarization模型
- **识别参数**：批处理大小、VAD参数、热词
- **输出配置**：置信度、时间戳、说话人标签

## 性能优化

1. **GPU加速**：设置 `--device cuda`
2. **批处理**：调整 `batch_size` 参数
3. **CPU优化**：设置 `ncpu` 参数
4. **内存管理**：配置 `max_file_size`
5. **并发处理**：使用异步处理多个请求

## 故障排除

### 1. 模型配置问题
如果遇到时间戳不支持的错误，应用会自动回退到基础识别模式：
```bash
# 默认使用支持时间戳的模型
python3 app.py --asr_model iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch

# 如果需要使用其他模型
python3 app.py --asr_model iic/SenseVoiceSmall
```

### 2. 模型下载问题
```bash
# 如果模型下载失败，可以手动下载
# 或者使用国内镜像源
export HF_ENDPOINT=https://hf-mirror.com
```

### 3. FFmpeg 安装
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### 4. 端口占用
```bash
# 检查端口占用
lsof -i :8001

# 杀死占用进程
kill -9 <PID>

# 或者使用其他端口
python3 app.py --port 8080
```

### 5. 内存不足
```bash
# 减少批处理大小
python3 app.py --batch_size 100

# 使用CPU模式
python3 app.py --device cpu
```

### 6. 依赖安装问题
如果遇到 pip 安装错误，尝试以下解决方案：
```bash
# 升级 pip
pip3 install --upgrade pip

# 使用国内源
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者使用阿里云源
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 清理缓存重试
pip3 cache purge
pip3 install -r requirements.txt
```

### 7. 日志调试
```bash
# 查看详细日志
tail -f astromao.log

# 或者直接在控制台查看
python3 app.py --log_level DEBUG
```