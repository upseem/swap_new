import pytz
import time
import uuid
import asyncio
import datetime
import shutil
from typing import Any
from itertools import count
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException,Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi import WebSocket, WebSocketDisconnect
from starlette.status import HTTP_403_FORBIDDEN


from config_loader import *
from utils import *
from log_config import setup_logging
from websocket_manager import WebSocketManager

# 初始化
logger  = setup_logging(config)
app     = FastAPI()

# 全局变量
server_address  = config["comfyui"]["server_address"]
swap_json       = config["comfyui"]["swap_json"]
root_dir        = config["storage"]["root_dir"]
timezone        = pytz.timezone(config["log"]["timezone"])
counter         = count(0)
client_id       = uuid.uuid4().hex
ws_manager      = WebSocketManager(server_address, client_id)
ws_manager.start_heartbeat(interval=10)  # 启动心跳机制，10秒一次

class SwapRequest(BaseModel):
    input_image: str
    source_image: str

class SwapResponse(BaseModel):
    code: int = 0
    message: str = ""
    data: Any = None


DELETE_ROOT = "/root/autodl-fs"
DELETE_SECRET = "cashbox..."

@app.middleware("http")
async def restrict_paths(request: Request, call_next):
    allowed_prefixes = ["/swap", "/ws", "/del"]
    path = request.url.path

    if not any(path.startswith(prefix) for prefix in allowed_prefixes):
        return JSONResponse(
            status_code=HTTP_403_FORBIDDEN,
            content={"detail": "hello"}
        )
    return await call_next(request)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass



import subprocess, os, time

# 后台异步删除函数（强制清空）
async def force_clear_dir(path: str):
    try:
        print(f"🚀 开始清空：{path}")
        
        # 第一步：删除所有文件 & 空目录（处理大批文件更快）
        subprocess.run(
            f"find {path} -type f -delete && find {path} -type d -empty -delete",
            shell=True, check=True
        )
        print(f"🔄 第一阶段清空完成：文件删除完毕")

        # 第二步：彻底删除整个目录（防止某些子目录未被删除）
        subprocess.run(f"rm -rf {path}", shell=True, check=True)
        print(f"🧹 第二阶段清空完成：目录已删除")

        # 第三步：重建空目录（保持路径存在）
        os.makedirs(path, exist_ok=True)
        print(f"✅ 清空彻底完成：{path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 删除失败: {e}")
        
@app.get("/del")
async def delete_all(
    secret: str = Query(...),
    subdir: str = Query(default="")
):
    if secret != DELETE_SECRET:
        raise HTTPException(status_code=403, detail="密钥错误")

    # 拼接路径（确保没有重复斜杠）
    path = os.path.join(DELETE_ROOT, subdir.strip("/")) if subdir else DELETE_ROOT

    # 后台异步删除任务
    asyncio.create_task(force_clear_dir(path))

    return {"status": f"🚀 删除任务已启动：{path}"}

    
@app.post("/swap", response_model=SwapResponse)
async def swap_faces(request: SwapRequest):
    input_base64 = None  # 提前声明
    try:
        current_count = next(counter)
        current_time = datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=========time:{current_time},开始:{current_count}=========")
        start_time = time.perf_counter()

        request.source_image = sanitize_url_yarl(request.source_image)
        request.input_image = sanitize_url_yarl(request.input_image)

        if not is_valid_url(request.source_image) or not is_valid_url(request.input_image):
            return SwapResponse(code=1000, message=f"Invalid image URL provided, 编号:{current_count}")

        logger.info(f"源图 URL: {request.source_image}")
        logger.info(f"目标图 URL: {request.input_image}")

        source_base64, input_base64 = await asyncio.gather(
            url_to_base64_and_down(request.source_image, root_dir),
            url_to_base64_and_down(request.input_image, root_dir)
        )

        if source_base64 is None or input_base64 is None:
            logger.warning(f"❌ 无法获取图片数据, 图片:{request.source_image},{request.input_image}, 编号:{current_count}")
            return SwapResponse(code=1000, message=f"图片URL获取失败, 编号:{current_count}")

        ws_manager.ensure_connected()
        prompt = load_json_to_dict(swap_json)
        prompt["251"]["inputs"]["base64_data"] = input_base64
        prompt["252"]["inputs"]["base64_data"] = source_base64

        prepare_time = time.perf_counter() - start_time
        logger.info(f"准备阶段耗时:{prepare_time:.2f}秒")

        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
        image = ws_manager.get_images(prompt_id)
        images_base64 = image_to_base64(image)

        elapsed_time = time.perf_counter() - start_time
        info = f"✅ Success,耗时:{elapsed_time:.2f}秒,id:{prompt_id}"
        logger.info(info)

        return SwapResponse(code=0, message=info, data={"image": images_base64})
    except Exception as e:
        
        if input_base64:
            logger.info(f"✅ Success ❌无脸 原图返回，异常，优先返回 input_base64(如果有: {str(e)}")
            return SwapResponse(code=0, message="异常，返回目标图", data={"image": input_base64})
        else:
            try:
                logger.warning(f"❌无脸，异常:无脸，正在下载原图返回 {str(e)}")
                fallback_base64 = await url_to_base64_and_down(request.input_image, root_dir)
                if fallback_base64:
                    return SwapResponse(code=0, message="异常，重新获取目标图返回", data={"image": fallback_base64})
                else:
                    return SwapResponse(code=1000, message="异常且获取原图失败",data={"image": ""})
            except Exception as ee:
                logger.warning(f"❌ 二次异常:请排查: {str(ee)}")
                return SwapResponse(code=1000, message="异常且二次获取原图失败", data={"image": ""}) 



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level=config["log"]["level"]
    )
