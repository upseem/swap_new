import os
import subprocess
from PIL import Image, ImageOps
import numpy as np
import comfy.utils
import folder_paths
import time
from io import BytesIO

class SaveImageWebsocket:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "jpeg_quality": (
                    "INT",
                    {
                        "default": 95,
                        "min": 60,
                        "max": 100,
                        "step": 1,
                        "tooltip": "JPEG压缩质量（1=低质量，100=高质量）"
                    },
                ),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "api/image"

    

    def save_images(self, images, jpeg_quality):
        temp_dir = folder_paths.get_output_directory()
        os.makedirs(temp_dir, exist_ok=True)
        pbar = comfy.utils.ProgressBar(images.shape[0])

        for idx, image in enumerate(images):
            try:
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                
                # 直接在内存中进行JPEG压缩，不写入临时文件
                buffer = BytesIO()
                # 直接使用PIL质量参数，不需要转换
                img.save(buffer, format="JPEG", quality=jpeg_quality)
                buffer.seek(0)
                jpg_img = Image.open(buffer)
                jpg_img = jpg_img.convert("RGB").copy()
                
                # 修改为与ws copy.py一致的格式，发送JPEG格式
                pbar.update_absolute(idx, images.shape[0], ("JPEG", jpg_img, None))
                
            except Exception as e:
                print(f"[SaveImageWebsocket] ❌ Skipped idx={idx} due to error: {e}")
                continue

        return {}


    @classmethod
    def IS_CHANGED(s, images, jpeg_quality):
        return time.time()

NODE_CLASS_MAPPINGS = {
    "SaveImageWebsocket": SaveImageWebsocket,
}
