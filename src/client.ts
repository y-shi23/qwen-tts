import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";
import { BASE_URL, VOICES, LANGUAGES } from "./constants";
import type { SynthesizeOptions, SynthesizeResult, SSEEventData } from "./types";

function getHeaders(): Record<string, string> {
  return {
    accept: "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    priority: "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-studio-token": "",
    Referer: "https://qwen-qwen3-tts-demo.ms.show/",
  };
}

async function predict(sessionHash: string): Promise<unknown> {
  const url = `${BASE_URL}/run/predict`;
  const headers = getHeaders();
  const data = {
    data: [0],
    event_data: null,
    fn_index: 0,
    trigger_id: 11,
    dataType: ["dataset"],
    session_hash: sessionHash,
  };

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

async function queueJoin(
  sessionHash: string,
  text: string,
  voice: string,
  language: string
): Promise<unknown> {
  const url = `${BASE_URL}/queue/join`;
  const headers = getHeaders();
  const data = {
    data: [text, voice, language],
    event_data: null,
    fn_index: 1,
    trigger_id: 7,
    dataType: ["textbox", "dropdown", "dropdown"],
    session_hash: sessionHash,
  };

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

async function queueData(sessionHash: string): Promise<string | null> {
  const url = `${BASE_URL}/queue/data`;
  const headers = getHeaders();
  headers.accept = "text/event-stream";

  const params = new URLSearchParams({
    session_hash: sessionHash,
    studio_token: "",
  });

  const response = await fetch(`${url}?${params.toString()}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let audioUrl: string | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const eventData: SSEEventData = JSON.parse(line.slice(6));
          const msg = eventData.msg;

          if (msg === "estimation") {
            const rank = eventData.rank || 0;
            const queueSize = eventData.queue_size || 0;
            const rankEta = eventData.rank_eta || 0;
            console.log(
              `队列位置: ${rank + 1}/${queueSize}, 预计等待: ${rankEta.toFixed(2)}秒`
            );
          } else if (msg === "process_starts") {
            console.log("开始处理...");
          } else if (msg === "process_completed") {
            console.log("处理完成!");
            const output = eventData.output;
            if (output?.data && output.data.length > 0) {
              const fileInfo = output.data[0];
              audioUrl = fileInfo.url || null;
              if (audioUrl) {
                console.log(`音频URL: ${audioUrl}`);
              }
            }
            return audioUrl;
          } else if (msg === "close_stream") {
            break;
          }
        } catch {
          continue;
        }
      }
    }
  }

  return audioUrl;
}

async function downloadAudio(
  audioUrl: string,
  outputPath: string
): Promise<string> {
  const headers = getHeaders();
  delete headers["content-type"];

  const response = await fetch(audioUrl, { headers });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(outputPath, buffer);
  console.log(`音频已保存到: ${outputPath}`);

  return outputPath;
}

export async function synthesize(
  options: SynthesizeOptions
): Promise<SynthesizeResult> {
  const {
    text,
    voice = "Cherry / 芊悦",
    language = "Chinese / 中文",
    outputPath = "output.wav",
    download = true,
  } = options;

  const sessionHash = crypto.randomUUID().replace(/-/g, "").slice(0, 12);
  console.log(`会话ID: ${sessionHash}`);
  console.log(`文本: ${text}`);
  console.log(`发音人: ${voice}`);
  console.log(`语言: ${language}`);
  console.log("-".repeat(50));

  console.log("步骤1: 初始化...");
  await predict(sessionHash);
  console.log("初始化完成");

  console.log("\n步骤2: 加入队列...");
  await queueJoin(sessionHash, text, voice, language);
  console.log("已加入队列");

  console.log("\n步骤3: 等待处理...");
  const audioUrl = await queueData(sessionHash);

  if (!audioUrl) {
    throw new Error("未能获取音频URL");
  }

  if (!download) {
    console.log(`\n音频URL（可直接播放）: ${audioUrl}`);
    return {
      success: true,
      message: "语音合成成功",
      audioUrl,
    };
  }

  console.log("\n步骤4: 下载音频...");
  const savedPath = await downloadAudio(audioUrl, outputPath);

  return {
    success: true,
    message: "语音合成成功",
    outputPath: savedPath,
    audioUrl,
  };
}

export { VOICES, LANGUAGES, BASE_URL };
