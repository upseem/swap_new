
#!/bin/bash

# 插件仓库配置：可指定 @tag 或 @branch，未指定则默认使用 main
declare -A repos_with_versions=(
  ["ComfyUI-Manager"]="https://github.com/Comfy-Org/ComfyUI-Manager.git"
  ["ComfyUI-Easy-Use"]="https://github.com/yolain/ComfyUI-Easy-Use.git"
  ["ICEdit-ComfyUI-official"]="https://github.com/hayd-zju/ICEdit-ComfyUI-official.git"
  ["ComfyUI-Impact-Pack"]="https://github.com/ltdrdata/ComfyUI-Impact-Pack.git@8.10"
  ["ComfyUI_LayerStyle"]="https://github.com/chflame163/ComfyUI_LayerStyle.git"
  ["rgthree-comfy"]="https://github.com/rgthree/rgthree-comfy.git@1.0.0"
  ["ComfyUI_InstantID"]="https://github.com/cubiq/ComfyUI_InstantID.git"
  ["was-node-suite-comfyui"]="https://github.com/WASasquatch/was-node-suite-comfyui.git@1.0.2"
  ["ComfyUI_essentials"]="https://github.com/cubiq/ComfyUI_essentials.git"  # 无 tag，使用默认分支
  ["ComfyUI-Impact-Subpack"]="https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git@1.2.9"
  ["comfyui_face_parsing"]="https://github.com/Ryuukeisyou/comfyui_face_parsing.git@1.0.5"
  ["comfyui_facetools"]="https://github.com/dchatel/comfyui_facetools.git"
)

INSTALL_DIR="/root/autodl-tmp/ComfyUI/custom_nodes"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR" || exit 1

# 安装 mediapipe
pip install mediapipe

# 分两步：1. clone 仓库；2. 统一 checkout
for name in "${!repos_with_versions[@]}"; do
  url_and_version="${repos_with_versions[$name]}"
  repo_url="${url_and_version%@*}"
  version="${url_and_version#*@}"

  if [ "$url_and_version" == "$repo_url" ]; then
    version=""
  fi

  if [ ! -d "$name" ]; then
    echo "🚀 Cloning $name..."
    git clone "$repo_url" "$name"
  else
    echo "✅ $name already exists, skipping clone."
  fi
done

# 第二步：切换版本（如果指定了）
for name in "${!repos_with_versions[@]}"; do
  url_and_version="${repos_with_versions[$name]}"
  version="${url_and_version#*@}"
  repo_url="${url_and_version%@*}"

  if [ "$url_and_version" == "$repo_url" ]; then
    version=""
  fi

  if [ -n "$version" ]; then
    echo "🔀 Trying to checkout $name to version/tag: $version"
    cd "$name" || continue
    if git rev-parse --verify "refs/tags/$version" > /dev/null 2>&1 || git rev-parse --verify "origin/$version" > /dev/null 2>&1; then
      git checkout "$version"
    else
      echo "⚠️  [$name] Version '$version' not found, using default branch."
    fi
    cd ..
  fi
done


# 安装各插件的依赖
for name in "${!repos_with_versions[@]}"; do
  if [ -f "$name/requirements.txt" ]; then
    echo "📦 Installing requirements for $name..."
    pip install -r "$name/requirements.txt"
  else
    echo "⚠️  No requirements.txt in $name"
  fi
done