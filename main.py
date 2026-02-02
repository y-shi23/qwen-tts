"""
Qwen TTS API 客户端
用于调用通义千问语音合成服务
"""

import json
import uuid
import requests


BASE_URL = "https://qwen-qwen3-tts-demo.ms.show/gradio_api"

# 可用的发音人列表
VOICES = [
    "Cherry / 芊悦",
    "Serena / 苏瑶",
    "Ethan / 晨煦",
    "Chelsie / 千雪",
    "Momo / 茉兔",
    "Vivian / 十三",
    "Moon / 月白",
    "Maia / 四月",
    "Kai / 凯",
    "Nofish / 不吃鱼",
    "Bella / 萌宝",
    "Jennifer / 詹妮弗",
    "Ryan / 甜茶",
    "Katerina / 卡捷琳娜",
    "Aiden / 艾登",
    "Bodega / 西班牙语-博德加",
    "Alek / 俄语-阿列克",
    "Dolce / 意大利语-多尔切",
    "Sohee / 韩语-素熙",
    "Ono Anna / 日语-小野杏",
    "Lenn / 德语-莱恩",
    "Sonrisa / 西班牙语拉美-索尼莎",
    "Emilien / 法语-埃米尔安",
    "Andre / 葡萄牙语欧-安德雷",
    "Radio Gol / 葡萄牙语巴-拉迪奥·戈尔",
    "Eldric Sage / 精品百人-沧明子",
    "Mia / 精品百人-乖小妹",
    "Mochi / 精品百人-沙小弥",
    "Bellona / 精品百人-燕铮莺",
    "Vincent / 精品百人-田叔",
    "Bunny / 精品百人-萌小姬",
    "Neil / 精品百人-阿闻",
    "Elias / 墨讲师",
    "Arthur / 精品百人-徐大爷",
    "Nini / 精品百人-邻家妹妹",
    "Ebona / 精品百人-诡婆婆",
    "Seren / 精品百人-小婉",
    "Pip / 精品百人-调皮小新",
    "Stella / 精品百人-美少女阿月",
    "Li / 南京-老李",
    "Marcus / 陕西-秦川",
    "Roy / 闽南-阿杰",
    "Peter / 天津-李彼得",
    "Eric / 四川-程川",
    "Rocky / 粤语-阿强",
    "Kiki / 粤语-阿清",
    "Sunny / 四川-晴儿",
    "Jada / 上海-阿珍",
    "Dylan / 北京-晓东",
]

# 可用的语言列表
LANGUAGES = [
    "Auto / 自动",
    "English / 英文",
    "Chinese / 中文",
    "German / 德语",
    "Italian / 意大利语",
    "Portuguese / 葡萄牙语",
    "Spanish / 西班牙语",
    "Japanese / 日语",
    "Korean / 韩语",
    "French / 法语",
    "Russian / 俄语",
]


def get_headers():
    """获取请求头"""
    return {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-studio-token": "",
        "Referer": "https://qwen-qwen3-tts-demo.ms.show/",
    }


def predict(session_hash: str):
    """初始化预测请求"""
    url = f"{BASE_URL}/run/predict"
    headers = get_headers()
    data = {
        "data": [0],
        "event_data": None,
        "fn_index": 0,
        "trigger_id": 11,
        "dataType": ["dataset"],
        "session_hash": session_hash,
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def queue_join(session_hash: str, text: str, voice: str, language: str):
    """加入队列请求"""
    url = f"{BASE_URL}/queue/join"
    headers = get_headers()
    data = {
        "data": [text, voice, language],
        "event_data": None,
        "fn_index": 1,
        "trigger_id": 7,
        "dataType": ["textbox", "dropdown", "dropdown"],
        "session_hash": session_hash,
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def queue_data(session_hash: str):
    """获取队列数据（SSE 流）"""
    url = f"{BASE_URL}/queue/data"
    headers = get_headers()
    headers["accept"] = "text/event-stream"

    params = {
        "session_hash": session_hash,
        "studio_token": "",
    }

    response = requests.get(
        url, headers=headers, params=params, stream=True, timeout=120
    )
    response.raise_for_status()

    audio_url = None
    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                try:
                    event_data = json.loads(line_str[6:])
                    msg = event_data.get("msg")

                    if msg == "estimation":
                        rank = event_data.get("rank", 0)
                        queue_size = event_data.get("queue_size", 0)
                        print(
                            f"队列位置: {rank + 1}/{queue_size}, 预计等待: {event_data.get('rank_eta', 0):.2f}秒"
                        )

                    elif msg == "process_starts":
                        print("开始处理...")

                    elif msg == "process_completed":
                        print("处理完成!")
                        output = event_data.get("output", {})
                        data = output.get("data", [])
                        if data and len(data) > 0:
                            file_info = data[0]
                            audio_url = file_info.get("url")
                            print(f"音频URL: {audio_url}")
                        return audio_url

                    elif msg == "close_stream":
                        break

                except json.JSONDecodeError:
                    continue

    return audio_url


def download_audio(audio_url: str, output_path: str = "output.wav"):
    """下载音频文件"""
    headers = get_headers()
    # 移除 content-type，下载文件不需要
    headers.pop("content-type", None)

    response = requests.get(audio_url, headers=headers, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"音频已保存到: {output_path}")
    return output_path


def synthesize(
    text: str,
    voice: str = "Cherry / 芊悦",
    language: str = "Chinese / 中文",
    output_path: str = "output.wav",
    download: bool = True,
):
    """
    合成语音

    Args:
        text: 要合成的文本
        voice: 发音人，默认为 "Cherry / 芊悦"
        language: 语言，默认为 "Chinese / 中文"
        output_path: 输出文件路径，默认为 "output.wav"
        download: 是否下载音频文件，默认为 True。如果为 False，则只返回音频URL

    Returns:
        如果 download=True，返回输出文件路径
        如果 download=False，返回音频URL（可直接播放，但有过期时间）
    """
    # 生成会话哈希
    session_hash = uuid.uuid4().hex[:12]
    print(f"会话ID: {session_hash}")
    print(f"文本: {text}")
    print(f"发音人: {voice}")
    print(f"语言: {language}")
    print("-" * 50)

    # 步骤1: 初始化
    print("步骤1: 初始化...")
    predict(session_hash)
    print("初始化完成")

    # 步骤2: 加入队列
    print("\n步骤2: 加入队列...")
    queue_join(session_hash, text, voice, language)
    print("已加入队列")

    # 步骤3: 获取数据并等待处理
    print("\n步骤3: 等待处理...")
    audio_url = queue_data(session_hash)

    if not audio_url:
        raise RuntimeError("未能获取音频URL")

    if not download:
        # 直接返回音频URL，可直接播放（但有过期时间）
        print(f"\n音频URL（可直接播放）: {audio_url}")
        return audio_url

    # 步骤4: 下载音频
    print("\n步骤4: 下载音频...")
    download_audio(audio_url, output_path)

    return output_path


def main():
    """主函数 - 示例用法"""
    # 示例1: 合成中文文本
    text = "你好，我是通义千问，很高兴认识你。"
    output = synthesize(text)
    print(f"\n合成完成: {output}")

    # 示例2: 使用不同的发音人和语言
    # text = "Hello, this is a test of English text to speech."
    # output = synthesize(
    #     text,
    #     voice="Jennifer / 詹妮弗",
    #     language="English / 英文",
    #     output_path="english_output.wav"
    # )
    # print(f"\n合成完成: {output}")


if __name__ == "__main__":
    main()
