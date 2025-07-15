import os
import re
import json  
import time
import base64 
import aiohttp
from yarl import URL
import urllib.request
from urllib.parse import urlparse  



# 定义URL有效性检查函数
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


def load_json_to_dict(filename):
    """从指定路径加载 JSON 文件并返回字典。

    参数:
    file_path (str): JSON 文件的路径。

    返回:
    dict: 加载的 JSON 数据字典。
    """
    # 获取当前文件的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构造完整路径
    file_path = os.path.join(current_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"文件不是有效的 JSON 格式: {file_path}")
        return {}


def remove_base64_header(base64_str):
    """
    检查并移除 Base64 字符串中的头部信息（如 data:image/jpeg;base64,）。
    如果不存在头部信息，则直接返回原始 Base64 字符串。
    """
    # 正则匹配 Base64 头部信息，如 data:image/jpeg;base64, 或其他格式
    base64_header_pattern = re.compile(r'^data:image\/[a-zA-Z]+;base64,')
    
    # 如果匹配到头部信息，则移除
    if base64_header_pattern.match(base64_str):
        # 使用正则去掉头部信息
        base64_str = base64_header_pattern.sub('', base64_str)
    
    return base64_str

# 定义将图片转换为Base64编码的函数
def image_to_base64(image: bytes) -> str:
    return base64.b64encode(image).decode('utf-8')



async def url_to_base64_and_down(url, root_dir):
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
            async with aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                }
            ) as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(local_path, "wb") as f:
                            f.write(content)
                        print(f"✅ 图片下载成功: {local_path}（耗时 {time.perf_counter() - start_time:.2f}s)")
                    else:
                        print(f"❌ 下载失败（状态码 {response.status}): {url}")
                        return None
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return None
    else:
        print(f"🟡 加载缓存图片: {local_path}")

    try:
        with open(local_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ 图片读取失败: {e}")
        return None
        
    
def queue_prompt(prompt, client_id: str, server_address: str, max_retries: int = 4, delay: float = 0.5):
    payload = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(payload).encode("utf-8")
    url = f"http://{server_address}/prompt"

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                raw = response.read()
                content = raw.decode("utf-8").strip()
                

                if not content:
                    raise ValueError("Empty response from server.")
                
                return json.loads(content)
        except Exception as e:
            print(f"[queue_prompt] Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise


def sanitize_url_yarl(url: str) -> str:
    """
    使用 yarl 安全处理 URL,移除路径中的多余 //，保留参数、锚点等
    """
    u = URL(url)
    clean_path = re.sub(r'/{2,}', '/', u.path)
    return u.with_path(clean_path).human_repr()