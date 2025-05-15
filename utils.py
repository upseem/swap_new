import os
import re
import json  
import base64 
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
