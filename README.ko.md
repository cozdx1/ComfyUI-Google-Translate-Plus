# ComfyUI Google Translate Plus

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

구글 번역 또는 로컬 CPU 모델로 프롬프트를 번역하면서 대사나 특정 문구를 그대로 보존합니다. 원문은 수정할 수 있고, 바로 아래에 읽기 전용 번역 결과가 표시됩니다.

노드 메뉴에서 `cozdx1`을 검색해 **[cozdx1] Google Translate Plus**를 추가합니다.

<p align="center">
  <img src="image/google-translate-plus.jpg" width="500" alt="자동 감지에서 영어로 번역하면서 따옴표와 백틱 안의 한국어를 보존한 노드">
</p>

<p align="center"><sub>주변 문장은 영어로 번역되고, 따옴표 안의 대사와 백틱 안의 문구는 한국어로 유지됩니다.</sub></p>

## 빠른 시작

1. **[cozdx1] Google Translate Plus**를 추가합니다.
2. 출발 언어와 도착 언어를 고릅니다. 기본값은 **자동 감지 → 영어**입니다.
3. 원문을 입력하고 `translated_text` 출력을 프롬프트 입력에 연결합니다.
4. Queue를 실행합니다. 번역 결과는 원문 아래에 표시됩니다.

Queue를 실행하면 원문을 자동으로 번역합니다. **Translate / 번역** 버튼은 실행 전에 결과를 미리 확인하는 용도입니다.

## 번역 제외 문구

기본값 **Quotes + backticks**는 아래 구간을 구분자까지 그대로 보존합니다.

- 큰따옴표: `"..."`, `“...”`, `「...」`, `『...』`.
- 백틱 한 개로 감싼 문구 또는 백틱 세 개로 감싼 여러 줄.

대사는 큰따옴표, 그 외 번역하지 않을 문구는 백틱으로 감싸면 편합니다. 작은따옴표는 번역 제외 대상이 아닙니다.

큰따옴표 안에서도 `(...)` 내용은 번역합니다. 예: `"안녕 (웃으며)"` → `"안녕 (smiling)"`. 백틱 안에서는 괄호 내용까지 모두 보존합니다.

### 테스트 문구

**자동 감지 → 영어**, **Quotes + backticks** 상태에서 아래 문구를 붙여넣습니다.

```text
여성이 카메라를 보며 손을 흔든다.
그녀가 "좋은 아침~ 오늘도 반가워요."라고 말한다.
배경의 표지판에는 `오늘도 좋은 하루`라고 적혀 있다.
```

스크린샷에 표시된 실제 결과입니다.

```text
A woman waves her hand while looking at the camera.
She says "좋은 아침~ 오늘도 반가워요.".
The sign in the background reads `오늘도 좋은 하루`.
```

| 모드 | 보존 대상 |
| --- | --- |
| `Quotes + backticks` | 큰따옴표와 백틱. |
| `Quotes only` | 큰따옴표. |
| `Backticks only` | 백틱. |
| `None` | 보존 없이 전체 번역. |

따옴표와 백틱은 짝을 맞춰 닫아 주세요.

## 인터페이스

- 구글 번역의 도착 언어 249개를 지원합니다.
- UI는 ComfyUI 언어 설정을 따릅니다. 영어·중국어·일본어·한국어를 지원합니다.
- 번역 결과는 워크플로와 함께 저장됩니다.
- 한 번에 최대 5,000자까지 번역합니다.
- Google은 모델 설치나 API 키 없이 사용하며 인터넷 연결이 필요합니다.
- Local OPUS-MT는 한 번 설치한 뒤 CPU로 오프라인 번역합니다. 두 엔진 모두 VRAM을 사용하지 않습니다.

## 설치

ComfyUI의 `custom_nodes` 폴더에서 실행합니다.

```sh
git clone https://github.com/cozdx1/ComfyUI-Google-Translate-Plus.git
```

ComfyUI를 재시작하고 브라우저를 새로고침합니다. 수동 설치를 업데이트하려면 설치한 폴더에서 `git pull`을 실행한 뒤 재시작하고 새로고침합니다.

## 로컬 CPU 번역

`backend`에서 **Local OPUS-MT (CPU)**를 선택하면 **한국어 → 영어**를 로컬로 번역합니다. 한국어 원문은 자동 감지로도 사용할 수 있으며, 영어 문장은 그대로 유지합니다.

- CPU INT8로 실행하며 VRAM·API 키·크레딧·외부 번역 요청을 사용하지 않습니다.
- 따옴표와 백틱을 보존하고, 따옴표 안의 괄호 내용은 번역합니다.
- 기본 엔진은 Google입니다. 로컬 모드는 한국어 → 영어만 지원합니다.

ComfyUI에서 사용하는 Python으로 **ComfyUI 폴더**에서 실행합니다.

```sh
python -m pip install "ctranslate2>=4.6,<5" "sentencepiece>=0.2,<1"
python custom_nodes/ComfyUI-Google-Translate-Plus/install_local_model.py --models-dir models
```

Windows 포터블은 `python` 대신 `..\python_embeded\python.exe`를 사용합니다.

설치 도구가 OPUS-MT 원본 약 777MB를 내려받아 체크섬을 확인하고, 약 222MB의 INT8 모델로 변환합니다. 저장 위치는 `models/translation/opus-mt-tc-big-ko-en-int8`입니다. 이미 설치된 모델은 유지합니다. 설치 후 ComfyUI를 재시작하고 브라우저를 새로고침합니다.

짧은 지시에 적합하며, 긴 문장은 주어나 세부 동작을 놓칠 수 있습니다. 보존 문구 앞뒤는 따로 번역하므로 문장 표현이 달라질 수 있습니다.

모델: [Helsinki-NLP OPUS-MT 한국어 → 영어](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-ko-en), **CC-BY-4.0**. 원본 Marian 가중치와 별도의 출발·도착 어휘집을 사용합니다.

## 개발

```sh
python -m unittest discover -s tests -v
node tests/test_frontend.cjs
```

## 라이선스

[MIT](LICENSE)
