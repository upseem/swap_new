import pytz
import time
import uuid
import asyncio
import datetime
from typing import Any
from itertools import count
from pydantic import BaseModel
from fastapi import FastAPI
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


@app.middleware("http")
async def restrict_paths(request: Request, call_next):
    # 只允许访问 /swap 和 /ws
    allowed_prefixes = ["/swap", "/ws"]
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
    
@app.post("/swap", response_model=SwapResponse)
async def swap_faces(request: SwapRequest):
    try:
        current_count = next(counter)
        current_time = datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=========time:{current_time},开始:{current_count}=========")
        start_time = time.perf_counter()

        if not is_valid_url(request.source_image) or not is_valid_url(request.input_image):
            return SwapResponse(code=1000, message=f"Invalid image URL provided, 编号:{counter}")

        logger.info(f"源图 URL: {request.source_image}")
        logger.info(f"目标图 URL: {request.input_image}")

        source_base64, input_base64 = await asyncio.gather(
            url_to_base64_and_down(request.source_image,root_dir),
            url_to_base64_and_down(request.input_image,root_dir)
        )

        if source_base64 is None or input_base64 is None:
            return SwapResponse(code=1000, message=f"图片URL获取失败, 编号:{current_count}")

        ws_manager.ensure_connected()
        prompt = load_json_to_dict(swap_json)
        prompt["251"]["inputs"]["base64_data"] = input_base64
        prompt["252"]["inputs"]["base64_data"] = source_base64

        prepare_time = time.perf_counter() - start_time
        logger.info(f"准备阶段耗时:{prepare_time:.2f}秒")

        prompt_id       = queue_prompt(prompt, client_id, server_address)['prompt_id']
        image           = ws_manager.get_images(prompt_id)
        images_base64   = image_to_base64(image)

        elapsed_time    = time.perf_counter() - start_time
        info = f"Success,耗时:{elapsed_time:.2f}秒,id:{prompt_id}"
        logger.info(info)


        return SwapResponse(code=0, message=info, data={"image": images_base64})
    except Exception as e:
        logger.warning(f"异常，返回原图: {str(e)}")
        return SwapResponse(code=0, message="异常原图返回", data={"image": request.input_image})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level=config["log"]["level"]
    )
