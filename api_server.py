"""
Qwen TTS API 服务器
提供 HTTP REST API 接口用于语音合成
"""

import os
import uuid
import tempfile
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from main import synthesize, VOICES, LANGUAGES


# 请求模型
class TTSRequest(BaseModel):
    text: str = Field(..., description="要合成的文本", min_length=1, max_length=5000)
    voice: str = Field(default="Cherry / 芊悦", description="发音人")
    language: str = Field(default="Chinese / 中文", description="语言")


# 响应模型
class TTSResponse(BaseModel):
    success: bool
    message: str
    file_url: Optional[str] = None
    text: str
    voice: str
    language: str


# 直接返回URL的响应模型
class TTSUrlResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    text: str
    voice: str
    language: str
    note: str


# 存储生成的音频文件
audio_files = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建临时目录
    app.state.temp_dir = tempfile.mkdtemp(prefix="qwen_tts_")
    print(f"临时文件目录: {app.state.temp_dir}")
    yield
    # 关闭时清理
    import shutil

    if os.path.exists(app.state.temp_dir):
        shutil.rmtree(app.state.temp_dir)
        print("临时文件已清理")


app = FastAPI(
    title="Qwen TTS API",
    description="通义千问语音合成 API 服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "Qwen TTS API",
        "version": "1.0.0",
        "description": "通义千问语音合成 API 服务",
        "endpoints": {
            "POST /tts": "语音合成（JSON 请求）",
            "GET /tts": "语音合成（Query 参数）",
            "POST /tts/url": "语音合成 - 直接返回音频URL（无需下载）",
            "GET /tts/url": "语音合成 - 直接返回音频URL（Query参数）",
            "GET /voices": "获取可用发音人列表",
            "GET /languages": "获取可用语言列表",
            "GET /audio/{file_id}": "下载音频文件",
        },
    }


@app.get("/voices")
async def get_voices():
    """获取可用发音人列表"""
    return {
        "voices": VOICES,
        "count": len(VOICES),
    }


@app.get("/languages")
async def get_languages():
    """获取可用语言列表"""
    return {
        "languages": LANGUAGES,
        "count": len(LANGUAGES),
    }


@app.post("/tts", response_model=TTSResponse)
async def tts_post(request: TTSRequest):
    """
    语音合成 - POST 方式

    请求体示例:
    ```json
    {
        "text": "你好，我是通义千问",
        "voice": "Cherry / 芊悦",
        "language": "Chinese / 中文"
    }
    ```
    """
    return await _do_synthesize(request.text, request.voice, request.language)


@app.get("/tts")
async def tts_get(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query(default="Cherry / 芊悦", description="发音人"),
    language: str = Query(default="Chinese / 中文", description="语言"),
):
    """
    语音合成 - GET 方式（适合简单测试）

    示例: /tts?text=你好&voice=Cherry%20/%20芊悦&language=Chinese%20/%20中文
    """
    return await _do_synthesize(text, voice, language)


@app.post("/tts/url", response_model=TTSUrlResponse)
async def tts_url_post(request: TTSRequest):
    """
    语音合成 - 直接返回音频URL（无需下载）

    返回的音频URL可直接播放，但有过期时间（通常几分钟到几小时）

    请求体示例:
    ```json
    {
        "text": "你好，我是通义千问",
        "voice": "Cherry / 芊悦",
        "language": "Chinese / 中文"
    }
    ```
    """
    return await _do_synthesize_url(request.text, request.voice, request.language)


@app.get("/tts/url")
async def tts_url_get(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query(default="Cherry / 芊悦", description="发音人"),
    language: str = Query(default="Chinese / 中文", description="语言"),
):
    """
    语音合成 - 直接返回音频URL（GET方式）

    示例: /tts/url?text=你好&voice=Cherry%20/%20芊悦
    """
    return await _do_synthesize_url(text, voice, language)


async def _do_synthesize(text: str, voice: str, language: str) -> TTSResponse:
    """执行语音合成"""
    # 验证参数
    if voice not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的发音人: {voice}。可用选项: {', '.join(VOICES[:5])}...",
        )

    if language not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的语言: {language}。可用选项: {', '.join(LANGUAGES)}",
        )

    try:
        # 生成文件 ID 和路径
        file_id = uuid.uuid4().hex
        output_path = os.path.join(app.state.temp_dir, f"{file_id}.wav")

        # 执行合成
        result_path = synthesize(
            text=text,
            voice=voice,
            language=language,
            output_path=output_path,
        )

        # 存储文件信息
        audio_files[file_id] = result_path

        return TTSResponse(
            success=True,
            message="语音合成成功",
            file_url=f"/audio/{file_id}",
            text=text,
            voice=voice,
            language=language,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


async def _do_synthesize_url(text: str, voice: str, language: str) -> TTSUrlResponse:
    """执行语音合成，直接返回音频URL"""
    # 验证参数
    if voice not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的发音人: {voice}。可用选项: {', '.join(VOICES[:5])}...",
        )

    if language not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的语言: {language}。可用选项: {', '.join(LANGUAGES)}",
        )

    try:
        # 执行合成，不下载文件，直接返回URL
        audio_url = synthesize(
            text=text,
            voice=voice,
            language=language,
            output_path="",  # 不需要输出路径
            download=False,  # 不下载，直接返回URL
        )

        return TTSUrlResponse(
            success=True,
            message="语音合成成功",
            audio_url=audio_url,
            text=text,
            voice=voice,
            language=language,
            note="此URL可直接播放，但有过期时间，建议尽快使用或自行下载保存",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


@app.get("/audio/{file_id}")
async def get_audio(file_id: str):
    """下载音频文件"""
    if file_id not in audio_files:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    file_path = audio_files[file_id]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")

    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=f"tts_{file_id}.wav",
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "qwen-tts-api"}


def main():
    """启动服务器"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
