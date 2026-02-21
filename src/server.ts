import * as crypto from "crypto";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import express, { Request, Response, NextFunction } from "express";
import { synthesize, VOICES, LANGUAGES } from "./client";
import type {
  TTSRequest,
  TTSResponse,
  TTSUrlResponse,
  VoicesResponse,
  LanguagesResponse,
} from "./types";

const app = express();
app.use(express.json());

const audioFiles: Map<string, string> = new Map();
let tempDir: string;

function ensureTempDir(): void {
  tempDir = path.join(os.tmpdir(), "qwen_tts_" + crypto.randomUUID().slice(0, 8));
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  console.log(`临时文件目录: ${tempDir}`);
}

function cleanupTempDir(): void {
  if (tempDir && fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
    console.log("临时文件已清理");
  }
}

process.on("SIGINT", () => {
  cleanupTempDir();
  process.exit(0);
});

process.on("SIGTERM", () => {
  cleanupTempDir();
  process.exit(0);
});

app.get("/", (_req: Request, res: Response) => {
  res.json({
    name: "Qwen TTS API",
    version: "1.0.0",
    description: "通义千问语音合成 API 服务",
    endpoints: {
      "POST /tts": "语音合成（JSON 请求）",
      "GET /tts": "语音合成（Query 参数）",
      "POST /tts/url": "语音合成 - 直接返回音频URL（无需下载）",
      "GET /tts/url": "语音合成 - 直接返回音频URL（Query参数）",
      "GET /voices": "获取可用发音人列表",
      "GET /languages": "获取可用语言列表",
      "GET /audio/{file_id}": "下载音频文件",
    },
  });
});

app.get("/voices", (_req: Request, res: Response) => {
  const response: VoicesResponse = {
    voices: VOICES,
    count: VOICES.length,
  };
  res.json(response);
});

app.get("/languages", (_req: Request, res: Response) => {
  const response: LanguagesResponse = {
    languages: LANGUAGES,
    count: LANGUAGES.length,
  };
  res.json(response);
});

app.post("/tts", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const request: TTSRequest = req.body;
    const result = await doSynthesize(request);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

app.get("/tts", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const request: TTSRequest = {
      text: req.query.text as string,
      voice: (req.query.voice as string) || "Cherry / 芊悦",
      language: (req.query.language as string) || "Chinese / 中文",
    };
    const result = await doSynthesize(request);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

app.post(
  "/tts/url",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const request: TTSRequest = req.body;
      const result = await doSynthesizeUrl(request);
      res.json(result);
    } catch (error) {
      next(error);
    }
  }
);

app.get(
  "/tts/url",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const request: TTSRequest = {
        text: req.query.text as string,
        voice: (req.query.voice as string) || "Cherry / 芊悦",
        language: (req.query.language as string) || "Chinese / 中文",
      };
      const result = await doSynthesizeUrl(request);
      res.json(result);
    } catch (error) {
      next(error);
    }
  }
);

async function doSynthesize(request: TTSRequest): Promise<TTSResponse> {
  const { text, voice = "Cherry / 芊悦", language = "Chinese / 中文" } = request;

  if (!VOICES.includes(voice)) {
    throw new Error(
      `无效的发音人: ${voice}。可用选项: ${VOICES.slice(0, 5).join(", ")}...`
    );
  }

  if (!LANGUAGES.includes(language)) {
    throw new Error(`无效的语言: ${language}。可用选项: ${LANGUAGES.join(", ")}`);
  }

  const fileId = crypto.randomUUID().replace(/-/g, "");
  const outputPath = path.join(tempDir, `${fileId}.wav`);

  const result = await synthesize({
    text,
    voice,
    language,
    outputPath,
    download: true,
  });

  if (result.outputPath) {
    audioFiles.set(fileId, result.outputPath);
  }

  return {
    success: true,
    message: "语音合成成功",
    file_url: `/audio/${fileId}`,
    text,
    voice,
    language,
  };
}

async function doSynthesizeUrl(request: TTSRequest): Promise<TTSUrlResponse> {
  const { text, voice = "Cherry / 芊悦", language = "Chinese / 中文" } = request;

  if (!VOICES.includes(voice)) {
    throw new Error(
      `无效的发音人: ${voice}。可用选项: ${VOICES.slice(0, 5).join(", ")}...`
    );
  }

  if (!LANGUAGES.includes(language)) {
    throw new Error(`无效的语言: ${language}。可用选项: ${LANGUAGES.join(", ")}`);
  }

  const result = await synthesize({
    text,
    voice,
    language,
    download: false,
  });

  return {
    success: true,
    message: "语音合成成功",
    audio_url: result.audioUrl,
    text,
    voice,
    language,
    note: "此URL可直接播放，但有过期时间，建议尽快使用或自行下载保存",
  };
}

app.get("/audio/:fileId", (req: Request, res: Response) => {
  const fileId = req.params.fileId;
  const filePath = audioFiles.get(fileId);

  if (!filePath) {
    res.status(404).json({ error: "文件不存在或已过期" });
    return;
  }

  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: "文件已被删除" });
    return;
  }

  res.download(filePath, `tts_${fileId}.wav`);
});

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "healthy", service: "qwen-tts-api" });
});

app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error("Error:", err.message);
  res.status(500).json({ error: `合成失败: ${err.message}` });
});

export function startServer(port: number = 8000): void {
  ensureTempDir();
  app.listen(port, () => {
    console.log(`Qwen TTS API 服务已启动: http://localhost:${port}`);
  });
}

export { app };
