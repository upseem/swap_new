import os
import re
import sys
import pytz
import time  
import uuid  
import json  
import base64 
import aiohttp
import asyncio
import logging
import requests
import datetime
import websocket  
import threading
import urllib.request 
from typing import Any
from fastapi import FastAPI  
from pydantic import BaseModel  
from urllib.parse import urlparse  

from config_loader import *
from utils import *
from log_config import setup_logging

# 获取配置
server_address  = config["comfyui"]["server_address"]
swap_json       = config["comfyui"]["swap_json"]
root_dir        = config["storage"]["root_dir"]

# 线上换脸程序，监听comfyui 实现同步返回接口 
app = FastAPI()

# 初始化全局计数器
counter = 0

client_id = str(uuid.uuid4())
ws = None
RETRY_DELAY = 1

# 时间
timezone        = pytz.timezone(config["log"]["timezone"])


logger = setup_logging(config)

class SwapRequest(BaseModel):
    input_image: str   # 输入图片的URL
    source_image: str  # 源图片的URL

class SwapResponse(BaseModel):
    code: int       = 0 # 返回代码,0表示成功, 1000失败
    message: str    = ""  # 返回的信息
    data: Any       = None  # 返回的图片数据，Base64编码


async def url_to_base64_and_down(url, root_dir=root_dir):
    """
    异步下载图片并缓存，返回 Base64 字符串（无头部）。
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme.startswith("http"):
        print(f"非法URL: {url}")
        return None

    sub_path = parsed_url.path.lstrip("/")
    local_path = os.path.join(root_dir, sub_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    if not os.path.exists(local_path):
        start_time = time.perf_counter()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(local_path, "wb") as f:
                            f.write(content)
                        elapsed = time.perf_counter() - start_time
                        print(f"图片下载成功: {local_path}（耗时 {elapsed:.2f}s)")
                    else:
                        print(f"下载失败（状态码 {response.status}): {url}")
                        return None
        except Exception as e:
            print(f"下载失败: {e}")
            return None
    else:
        print(f"加载缓存图片: {local_path}")

    # base64 编码本地图片
    try:
        with open(local_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"图片读取失败: {e}")
        return None


# 定义WebSocket连接函数，带有异常处理但不抛出HTTPException，以便进行重试
def connect_websocket():
    logging.info("进来connect_websocket:尝试连接ws")
    global ws
    try:
        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
        print("ws连接成功:WebSocket connected.")
        logger.info("ws连接成功:WebSocket connected.")
    except (websocket.WebSocketException, ConnectionRefusedError) as e:
        print(f"ws连接失败,WebSocket connection failed: {e}")
        logger.error(f"ws连接失败,WebSocket connection failed: {e}")
        ws = None

# 通用的 WebSocket 连接检查函数，允许控制是否定时循环检测
def check_ws_connection(is_periodic=False, interval=5):
    global ws
    while True:
        try:
            if ws is None or not ws.connected:
                print("WebSocket disconnected, reconnecting...")
                logger.error("check_ws_connection: WebSocket disconnected, reconnecting...")
                connect_websocket()
            else:
                ws.send("ping")  # 发送 ping 命令确保连接活跃
                # logger.info("WebSocket connection is alive.")
        except (websocket.WebSocketException, BrokenPipeError) as e:
            print(f"WebSocket error: {e}, reconnecting...")
            logger.error(f"check_ws_connection: WebSocket error: {e}, reconnecting...")
            connect_websocket()
        except ConnectionRefusedError as e:
            print(f"Connection refused: {e}")
            logger.error(f"check_ws_connection: Connection refused: {e}, retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)  # 延迟一段时间后重试连接
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"check_ws_connection: Unexpected error: {e}, reconnecting...")
            connect_websocket()

        # 如果是定时任务，则每隔指定时间检测一次
        if is_periodic:
            time.sleep(interval)
        else:
            break  # 非定时任务时，执行一次后退出

# 定义最大重试次数和每次重试的等待时间
MAX_RETRIES = 4
RETRY_DELAY = 0.5  # 每次重试之间等待2秒

# 启动WebSocket连接检查线程
ws_thread = threading.Thread(target=check_ws_connection, args=(True, 5))
ws_thread.daemon = True  # 设置为守护线程，随主线程退出而退出
ws_thread.start()

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')  # 将Python对象转换为JSON字符串并编码
    url = "http://{}/prompt".format(server_address)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 创建请求对象
            req = urllib.request.Request(url, data=data)
            
            # 发起请求并获取响应
            response = urllib.request.urlopen(req)
            return json.loads(response.read())  # 解析并返回JSON响应
        
        except Exception as e:
            # 打印错误信息并检查重试次数
            print(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                logger.error(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)  # 等待一段时间后重试
            else:
                print("Max retries reached. Failing.")
                logger.error("Max retries reached. Failing.")
                raise  # 如果达到最大重试次数，抛出异常

# 定义获取图片的函数
def get_images(ws, prompt_id):
    output_image = None  # 用于存储返回的图片
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                # print(data)  # 打印执行过程中的数据
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break  # 执行完成，退出循环
                    else:
                        current_node = data['node']
        else:
            if current_node == 'save_image_websocket_node':
                # 只存储接收到的第一张图片
                if output_image is None:
                    output_image = out[8:]  # 去掉前8个字节的头部信息
    return output_image

def ensure_ws_connected():
    global ws
    if ws is None or not ws.connected:
        logger.warning("WS not connected, reconnecting...")
        connect_websocket()
        

# 定义用于换脸的API接口
@app.post("/swap", response_model=SwapResponse)
async def swap_faces(request: SwapRequest):
    try:
        # 获取当前时间，并转换为东八区时间
        current_time = datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

        global counter 
        print(f"=========time:{current_time},开始:{counter}=========")
        start_time = time.perf_counter()

        # 验证两个URL是否都有效
        if not is_valid_url(request.source_image) or not is_valid_url(request.input_image):
            return SwapResponse(code=1000, message=f"Invalid image URL provided, 编号:{counter}")

        print(f"源图 URL: {request.source_image}")
        print(f"目标图 URL: {request.input_image}")
        
        # 下载并转换为 base64（异步并行）
        source_base64, input_base64 = await asyncio.gather(
            url_to_base64_and_down(request.source_image),
            url_to_base64_and_down(request.input_image)
        )

        if source_base64 is None or input_base64 is None:
            return SwapResponse(code=1000, message=f"图片URL获取失败, 编号:{counter}")

        # check_ws_connection()  # 每次请求前确保WebSocket连接正常
        ensure_ws_connected()
        prompt = load_json_to_dict(swap_json)

        # 插入到提示字典
        prompt["251"]["inputs"]["base64_data"] = input_base64
        prompt["252"]["inputs"]["base64_data"] = source_base64

        # 发送任务队列前记录耗时
        prepare_time = time.perf_counter() - start_time
        print(f"准备阶段耗时(图片下载 + prompt构建):{prepare_time:.2f}秒")
        # 发送任务队列
        prompt_id = queue_prompt(prompt)['prompt_id']

        # 获取处理结果图像
        image = get_images(ws, prompt_id)
        images_base64 = image_to_base64(image)

        elapsed_time = time.perf_counter() - start_time
        info = f"Success,耗时:{elapsed_time:.2f}秒,id:{prompt_id}"
        print(info)

        counter += 1
        return SwapResponse(code=0, message=info, data={"image": images_base64})
    except Exception as e:
        print(f"异常，返回原图: {str(e)}")
        return SwapResponse(code=0, message="Success", data={"image": request.input_image})

# 启动FastAPI应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level=config["log"]["level"]
    )
