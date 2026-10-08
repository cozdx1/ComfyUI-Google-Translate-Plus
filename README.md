# ComfyUI Google Translate Plus

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

Translate prompts with Google Translate while keeping dialogue and selected phrases unchanged. The source text stays editable, and a read-only translation appears directly below it.

Search for `cozdx1` in the node menu and add **[cozdx1] Google Translate Plus**.

<p align="center">
  <img src="image/google-translate-plus.jpg" width="500" alt="Automatic language detection, English output, and preserved Korean quotes and backticks">
</p>

<p align="center"><sub>The surrounding sentences are translated into English. Quoted dialogue and the phrase inside backticks stay in Korean.</sub></p>

## Quick start

1. Add **[cozdx1] Google Translate Plus**.
2. Choose the source and target languages. Defaults: **Auto-detect → English**.
3. Enter the source text and connect `translated_text` to a prompt input.
4. Run Queue. The translation appears below the source text.

Queue translates the source text automatically. The **Translate** button previews the result before running the workflow.

## Protected text

The default **Quotes + backticks** mode preserves these sections, including the delimiters:

- Double quotes: `"..."`, `“...”`, `「...」`, and `『...』`.
- Single backticks for a phrase, or triple backticks for multiple lines.

Use double quotes for dialogue and backticks for other phrases you want to keep. Single quotation marks do not exclude text from translation.

### Try it

Paste this text with **Auto-detect → English** and **Quotes + backticks**:

```text
여성이 카메라를 보며 손을 흔든다.
그녀가 "좋은 아침~ 오늘도 반가워요."라고 말한다.
배경의 표지판에는 `오늘도 좋은 하루`라고 적혀 있다.
```

The screenshot shows this result:

```text
A woman waves her hand while looking at the camera.
She says "좋은 아침~ 오늘도 반가워요.".
The sign in the background reads `오늘도 좋은 하루`.
```

| Mode | Preserves |
| --- | --- |
| `Quotes + backticks` | Double quotes and backticks. |
| `Quotes only` | Double quotes. |
| `Backticks only` | Backticks. |
| `None` | Nothing; translates the entire text. |

Close each pair of quotes or backticks.

## Interface

- Supports 249 Google Translate target languages.
- The UI follows ComfyUI's language setting. English, Chinese, Japanese, and Korean are supported.
- Translations are saved with the workflow.
- Up to 5,000 source characters per request.
- No model installation, API key, or VRAM use.
- An internet connection is required.

## Installation

From the ComfyUI `custom_nodes` directory:

```sh
git clone https://github.com/cozdx1/ComfyUI-Google-Translate-Plus.git
```

Restart ComfyUI and refresh the browser. To update a manual installation, run `git pull` in the cloned directory, then restart and refresh.

## Development

```sh
python -m unittest discover -s tests -v
node tests/test_frontend.cjs
```

## License

[MIT](LICENSE)
