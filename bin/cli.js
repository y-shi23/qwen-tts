#!/usr/bin/env node

const path = require("path");

const args = process.argv.slice(2);
const command = args[0];

if (command === "server" || path.basename(process.argv[1]) === "qwen-tts-server") {
  require("../dist/server.js").startServer(8000);
} else {
  const { synthesize, VOICES, LANGUAGES } = require("../dist/client.js");

  function printUsage() {
    console.log(`
用法: qwen-tts [选项]

选项:
  -t, --text <text>       要合成的文本 (必需)
  -v, --voice <voice>     发音人 (默认: Cherry / 芊悦)
  -l, --language <lang>   语言 (默认: Chinese / 中文)
  -o, --output <path>     输出文件路径 (默认: output.wav)
  --list-voices           列出所有可用发音人
  --list-languages        列出所有可用语言
  --url                   只返回音频URL，不下载
  server                  启动 HTTP API 服务器
  -h, --help              显示帮助信息
`);
  }

  function listVoices() {
    console.log("可用发音人:");
    VOICES.forEach((voice) => console.log(`  - ${voice}`));
  }

  function listLanguages() {
    console.log("可用语言:");
    LANGUAGES.forEach((lang) => console.log(`  - ${lang}`));
  }

  async function main() {
    if (args.includes("--help") || args.includes("-h")) {
      printUsage();
      process.exit(0);
    }

    if (args.includes("--list-voices")) {
      listVoices();
      process.exit(0);
    }

    if (args.includes("--list-languages")) {
      listLanguages();
      process.exit(0);
    }

    const textIndex = args.findIndex((a) => a === "-t" || a === "--text");
    const voiceIndex = args.findIndex((a) => a === "-v" || a === "--voice");
    const langIndex = args.findIndex((a) => a === "-l" || a === "--language");
    const outputIndex = args.findIndex((a) => a === "-o" || a === "--output");
    const urlOnly = args.includes("--url");

    const text = textIndex >= 0 ? args[textIndex + 1] : undefined;

    if (!text) {
      console.error("错误: 请提供要合成的文本 (-t, --text)");
      printUsage();
      process.exit(1);
    }

    const voice = voiceIndex >= 0 ? args[voiceIndex + 1] : "Cherry / 芊悦";
    const language = langIndex >= 0 ? args[langIndex + 1] : "Chinese / 中文";
    const outputPath = outputIndex >= 0 ? args[outputIndex + 1] : "output.wav";

    try {
      const result = await synthesize({
        text,
        voice,
        language,
        outputPath,
        download: !urlOnly,
      });

      if (urlOnly && result.audioUrl) {
        console.log(`\n音频URL: ${result.audioUrl}`);
      } else if (result.outputPath) {
        console.log(`\n合成完成: ${result.outputPath}`);
      }
    } catch (error) {
      console.error("合成失败:", error.message);
      process.exit(1);
    }
  }

  main();
}
