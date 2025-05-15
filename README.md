git clone https://github.com/comfyanonymous/ComfyUI.git 
cd ComfyUI
git checkout v0.3.34

cd custom_nodes/
conda create -n swap python=3.12
conda activate swap


pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121


pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124

pip install -r requirements.txt




python main.py --listen 0.0.0.0 --port 6006 

ultralytics


model:
大模型
face_tools: 
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/landmarks .         https://huggingface.co/bluefoxcreation/FaceAlignment
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/bisenet .           https://drive.google.com/file/d/154JgKpzCPW82qINcVieuPH3fZ2e0P812/view

sam: 
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/sams .
https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/sams/sam_vit_b_01ec64.pth

ln -s /root/autodl-tmp/model_hub/comfyui_model/models/ultralytics .

instantid: ip-adapter.bin
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/instantid/sdxl_models .   
https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin

ln -s /root/autodl-tmp/model_hub/comfyui_model/models/insightface/models .  wget https://github.com/deepinsight/insightface/releases/download/v0.7/antelopev2.zip -O antelopev2.zip

controlnet: models/controlnet/SDXL   
ln -s /root/autodl-tmp/model_hub/comfyui_model/models/controlnet/SDXL/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors . 
https://huggingface.co/TTPlanet/TTPLanet_SDXL_Controlnet_Tile_Realistic/resolve/main/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors

ln -s /root/autodl-tmp/model_hub/comfyui_model/models/controlnet/SDXL/control_instant_id_sdxl.safetensors .   
https://huggingface.co/dominic1021/controls/resolve/main/control_instant_id_sdxl.safetensors


face_parsing/model.safetensors



git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
git clone https://github.com/chflame163/ComfyUI_LayerStyle.git
git clone https://github.com/rgthree/rgthree-comfy.git
git clone https://github.com/cubiq/ComfyUI_InstantID.git
git clone https://github.com/WASasquatch/was-node-suite-comfyui.git
git clone https://github.com/cubiq/ComfyUI_essentials.git
git clone https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git
git clone https://github.com/Ryuukeisyou/comfyui_face_parsing.git
git clone https://github.com/dchatel/comfyui_facetools.git

