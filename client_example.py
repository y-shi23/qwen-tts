"""
Qwen TTS API 客户端示例
演示如何调用 API 进行语音合成
"""

import requests
import sys

# API 基础 URL
BASE_URL = "http://localhost:8000"


def list_voices():
    """获取可用发音人列表"""
    response = requests.get(f"{BASE_URL}/voices")
    data = response.json()
    print("可用发音人:")
    for voice in data["voices"]:
        print(f"  - {voice}")


def list_languages():
    """获取可用语言列表"""
    response = requests.get(f"{BASE_URL}/languages")
    data = response.json()
    print("可用语言:")
    for lang in data["languages"]:
        print(f"  - {lang}")


def synthesize_text(
    text: str, voice: str = "Cherry / 芊悦", language: str = "Chinese / 中文"
):
    """
    合成文本为语音

    Args:
        text: 要合成的文本
        voice: 发音人
        language: 语言
    """
    # 方式1: POST 请求（推荐）
    payload = {
        "text": text,
        "voice": voice,
        "language": language,
    }

    print(f"正在合成: {text}")
    print(f"发音人: {voice}")
    print(f"语言: {language}")
    print("-" * 50)

    response = requests.post(f"{BASE_URL}/tts", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"合成成功!")
        print(f"消息: {data['message']}")
        print(f"音频地址: {BASE_URL}{data['file_url']}")

        # 下载音频文件
        audio_response = requests.get(f"{BASE_URL}{data['file_url']}")
        if audio_response.status_code == 200:
            filename = "output_client.wav"
            with open(filename, "wb") as f:
                f.write(audio_response.content)
            print(f"音频已保存到: {filename}")
            return filename
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)
        return None


def synthesize_text_get(
    text: str, voice: str = "Cherry / 芊悦", language: str = "Chinese / 中文"
):
    """使用 GET 请求合成（适合简单测试）"""
    params = {
        "text": text,
        "voice": voice,
        "language": language,
    }

    response = requests.get(f"{BASE_URL}/tts", params=params)
    return response.json()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Qwen TTS API 客户端")
    parser.add_argument(
        "--text", "-t", default="你好，我是通义千问", help="要合成的文本"
    )
    parser.add_argument("--voice", "-v", default="Cherry / 芊悦", help="发音人")
    parser.add_argument("--language", "-l", default="Chinese / 中文", help="语言")
    parser.add_argument("--list-voices", action="store_true", help="列出可用发音人")
    parser.add_argument("--list-languages", action="store_true", help="列出可用语言")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if args.list_languages:
        list_languages()
        return

    # 合成文本
    synthesize_text(args.text, args.voice, args.language)


if __name__ == "__main__":
    main()
