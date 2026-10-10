# ComfyUI Google Translate Plus

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

使用Google翻译或本地CPU模型翻译提示词，同时保留对白和指定短语。原文可编辑，翻译结果直接显示在下方的只读文本框中。

在节点菜单搜索 `cozdx1`，添加 **[cozdx1] Google Translate Plus**。

<p align="center">
  <img src="image/google-translate-plus.jpg" width="500" alt="自动检测原文并翻译成英语，同时保留引号和反引号内韩语的节点">
</p>

<p align="center"><sub>周围的句子被翻译成英语。引号内的对白和反引号内的短语保持韩语不变。</sub></p>

## 快速开始

1. 添加 **[cozdx1] Google Translate Plus**。
2. 选择源语言和目标语言。默认是 **自动检测 → 英语**。
3. 输入原文，将 `translated_text` 输出连接到提示词输入。
4. 运行Queue。翻译结果显示在原文下方。

Queue自动翻译原文。**Translate / 翻译** 按钮用于在运行前预览结果。

## 保护文本

默认的 **Quotes + backticks** 模式保留以下分隔符内的文本，并保留分隔符本身。

- 双引号：`"..."`、`“...”`、`「...」`、`『...』`。
- 单个反引号包围的短语，或三个反引号包围的多行文本。

对白可用双引号，其他不想翻译的短语可用反引号。单引号不属于翻译排除范围。

即使在引号内，`(...)` 中的内容也会翻译。例如：`"안녕 (웃으며)"` → `"안녕 (smiling)"`。反引号内的所有内容（包括括号内容）保持不变。

### 测试文本

使用 **自动检测 → 英语** 和 **Quotes + backticks**，粘贴以下文本。

```text
여성이 카메라를 보며 손을 흔든다.
그녀가 "좋은 아침~ 오늘도 반가워요."라고 말한다.
배경의 표지판에는 `오늘도 좋은 하루`라고 적혀 있다.
```

截图中的实际结果如下。

```text
A woman waves her hand while looking at the camera.
She says "좋은 아침~ 오늘도 반가워요.".
The sign in the background reads `오늘도 좋은 하루`.
```

| 模式 | 保留内容 |
| --- | --- |
| `Quotes + backticks` | 双引号和反引号。 |
| `Quotes only` | 双引号。 |
| `Backticks only` | 反引号。 |
| `None` | 不保留，翻译全部文本。 |

引号和反引号请成对闭合。

## 界面

- 支持Google翻译的249种目标语言。
- UI跟随ComfyUI语言设置，支持英语、中文、日语和韩语。
- 翻译结果随工作流保存。
- 每次最多翻译5,000个字符。
- Google无需安装模型或API密钥，但需要互联网连接。
- Local OPUS-MT安装一次后即可在CPU上离线翻译。两种引擎均不占用VRAM。

## 安装

在ComfyUI的 `custom_nodes` 目录中运行：

```sh
git clone https://github.com/cozdx1/ComfyUI-Google-Translate-Plus.git
```

重启ComfyUI并刷新浏览器。手动安装的更新方式是在安装目录运行 `git pull`，然后重启并刷新。

## 本地CPU翻译

在`backend`中选择 **Local OPUS-MT (CPU)**，即可在本地进行**韩语 → 英语**翻译。韩语输入也可选择自动检测，英语文本保持不变。

- 使用CPU INT8，不占用VRAM，无需API密钥、积分或外部翻译请求。
- 保留引号和反引号，引号内括号的内容仍会翻译。
- 默认引擎为Google。本地模式仅支持韩语 → 英语。

使用ComfyUI的Python，在 **ComfyUI文件夹**中运行：

```sh
python -m pip install "ctranslate2>=4.6,<5" "sentencepiece>=0.2,<1"
python custom_nodes/ComfyUI-Google-Translate-Plus/install_local_model.py --models-dir models
```

Windows便携版请将`python`替换为`..\python_embeded\python.exe`。

安装工具下载约777MB的原始模型，验证校验和后转换为约222MB的INT8模型。保存位置为`models/translation/opus-mt-tc-big-ko-en-int8`。已安装的模型会保留。安装后重启ComfyUI并刷新浏览器。

适合简短指令。较长的句子可能遗漏主语或细节。保护文本前后会分别翻译，可能影响措辞。

模型：[Helsinki-NLP OPUS-MT 韩语 → 英语](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-ko-en)，**CC-BY-4.0**。使用原始Marian权重及独立的源语言和目标语言词表。

## 开发

```sh
python -m unittest discover -s tests -v
node tests/test_frontend.cjs
```

## 许可证

[MIT](LICENSE)
