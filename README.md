
# ComfyUI FaceSwap API 部署指南

基于 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 构建，结合多种人脸处理工具，实现换脸任务，并通过 FastAPI 提供接口服务。

## ✅ 环境准备

### 1. 克隆主程序并切换版本

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
git checkout v0.3.34
```

### 2. 创建 Python 环境

建议使用 Anaconda:

```bash
conda create -n swap python=3.12 -y
conda activate swap
```

### 3. 安装 PyTorch（根据你显卡的 CUDA 版本选择一项）

| CUDA | 安装命令                                                                                                                |
| ---- | ------------------------------------------------------------------------------------------------------------------- |
| 12.4 | `pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124` |
| 12.1 | `pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121` |
| 11.8 | `pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118` |

---

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

---

## 🔗 模型结构链接（软链接）

将以下模型下载并软链接到 ComfyUI 的 `models/` 子目录中（示例路径基于 `/root/autodl-tmp/model_hub/comfyui_model/`）：

```bash
# 进入 ComfyUI 自定义节点目录
cd ComfyUI/custom_nodes

# landmarks
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/landmarks .

# bisenet
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/bisenet .

# sams
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/sams .

# ultralytics (YOLOv8)
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/ultralytics .

# instantid
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/instantid/sdxl_models .

# insightface
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/insightface/models .

# controlnet (TTPlanet/InstantID)
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/controlnet/SDXL/control_instant_id_sdxl.safetensors .
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/controlnet/SDXL/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors .

# face_parsing
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/face_parsing/model.safetensors .
```

---

## 🧩 安装插件节点

```bash
cd ComfyUI/custom_nodes

git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
git clone https://github.com/chflame163/ComfyUI_LayerStyle.git
git clone https://github.com/rgthree/rgthree-comfy.git
git clone https://github.com/cubiq/ComfyUI_InstantID.git
git clone https://github.com/WASasquatch/was-node-suite-comfyui.git
git clone https://github.com/cubiq/ComfyUI_essentials.git
git clone https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git
git clone https://github.com/Ryuukeisyou/comfyui_face_parsing.git
git clone https://github.com/dchatel/comfyui_facetools.git
```

---

## 🚀 启动 ComfyUI 服务

```bash
python main.py --listen 0.0.0.0 --port 6006
```

---

## 🧠 FastAPI换脸接口服务

你可以通过 `main.py` 启动换脸接口服务：

```bash
python api/main.py
```

默认监听地址为：

```
http://0.0.0.0:6006/swap
```

---

## 📁 项目结构简览

```
ComfyUI/
├── custom_nodes/
│   ├── comfyui_facetools/
│   ├── ComfyUI-Impact-Pack/
│   └── ...
├── models/
│   ├── landmarks/
│   ├── bisenet/
│   └── ...
api/
├── main.py
├── log_config.py
├── websocket_manager.py
├── utils.py
└── config_loader.py
```

---

## 📌 配置说明 (`config.yaml`)

```yaml
comfyui:
  server_address: 127.0.0.1:6006
  swap_json: data/swap.json

storage:
  root_dir: ./cache_images

log:
  level: info
  timezone: Asia/Shanghai
  directory: ./logs
  filename_prefix: swap
  retention_days: 30

server:
  host: 0.0.0.0
  port: 6006
```




### 🧰 Supervisor 管理指令

使用 Supervisor 启动、管理 ComfyUI 和 AI-Swap 服务：

#### 启动 Supervisor

```bash
supervisord -c /etc/supervisor/supervisord.conf
```

#### 查看所有服务状态

```bash
supervisorctl status
```

#### 启动 / 重启单个服务

```bash
supervisorctl start comfyui
supervisorctl start ai-swap

supervisorctl restart comfyui
supervisorctl restart ai-swap
```

#### 停止服务

```bash
supervisorctl stop comfyui
supervisorctl stop ai-swap
```

---

### 📜 日志查看

#### 查看 ComfyUI 的运行日志

```bash
tail -f /var/log/comfyui.out.log
```

#### 查看 AI-Swap 的运行日志

```bash
tail -f /var/log/swap_api.out.log
```

#### 查看错误日志

```bash
tail -f /var/log/comfyui.err.log
tail -f /var/log/swap_api.err.log
```

