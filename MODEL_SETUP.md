# 模型设置指南

## 概述

本项目现在支持本地模型缓存，可以预先下载模型到本地，避免每次启动时重新下载。

## 快速开始

### 1. 下载模型

在项目根目录下运行以下命令下载所需的模型：

```bash
python download_models.py
```

这个脚本会自动下载以下模型到 `models/` 文件夹：

- **语音识别模型**: `speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch`（支持时间戳）
- **VAD模型**: `speech_fsmn_vad_zh-cn-16k-common-pytorch`
- **标点符号模型**: `punc_ct-transformer_zh-cn-common-vocab272727-pytorch`
- **说话人识别模型**: `speech_campplus_sv_zh-cn_16k-common`
- **语音分离模型**: `speech_diarization_sond-zh-cn-alimeeting-16k-n16k4-pytorch`

### 2. 启动应用

模型下载完成后，正常启动应用：

```bash
python app.py
```

应用会自动检查本地模型是否存在，如果模型文件缺失，会提示您先运行下载脚本。

## 文件结构

```
astromao/
├── models/                                    # 本地模型存储目录
│   ├── speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch/
│   ├── speech_fsmn_vad_zh-cn-16k-common-pytorch/
│   ├── punc_ct-transformer_zh-cn-common-vocab272727-pytorch/
│   ├── speech_campplus_sv_zh-cn_16k-common/
│   └── speech_diarization_sond-zh-cn-alimeeting-16k-n16k4-pytorch/
├── download_models.py                         # 模型下载脚本
├── app.py                                     # 主应用程序
└── requirements.txt                           # 依赖列表
```

## 优势

1. **离线使用**: 模型下载后可以完全离线使用
2. **启动速度**: 避免每次启动时重新下载模型
3. **稳定性**: 不依赖网络连接的稳定性
4. **版本控制**: 固定模型版本，确保结果一致性

## 故障排除

### 模型下载失败

如果模型下载失败，请检查：

1. 网络连接是否正常
2. 是否安装了 `modelscope` 库：
   ```bash
   pip install modelscope
   ```
3. 磁盘空间是否充足（模型文件较大，约需要几GB空间）

### 启动时提示模型不存在

如果启动时提示模型文件不存在，请：

1. 确认已运行 `python download_models.py`
2. 检查 `models/` 文件夹是否存在且包含模型文件
3. 如果模型下载不完整，删除 `models/` 文件夹后重新下载

## 自定义模型路径

如果需要使用不同的模型或路径，可以在启动时指定：

```bash
python app.py --asr_model /path/to/your/asr/model --vad_model /path/to/your/vad/model --punc_model /path/to/your/punc/model
```

## 注意事项

- 首次下载模型需要较长时间和网络连接
- 模型文件较大，请确保有足够的磁盘空间
- 建议在稳定的网络环境下进行模型下载