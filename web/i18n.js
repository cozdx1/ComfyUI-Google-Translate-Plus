export const messages = {
    en: {
        backend: "Translation engine. Local OPUS-MT uses CPU only and supports Korean to English.",
        local_language: "Local OPUS-MT supports Korean to English only. Select Korean or Auto-detect → English.",
        local_setup: "The local CPU model or its dependencies are missing. Check the local installation.",
        local_output: "The local model could not complete the translation. Split the text into shorter sentences.",
        limited: "Translate · Rate limited", rate_limit: "Google Translate temporarily rejected the request (HTTP 429). Wait before trying again; the reset time is unknown.",
        translate: "Translate", busy: "Translating…", done: "Translate · Done", changed: "Translate · Changed", error: "Translate · Error (retry)",
        placeholder: "Translation result. Queue translates automatically; Translate previews it.",
        readonly: "Read-only translation result.", auto: "Auto-detect",
        source: "Language of the source text. Auto-detect identifies it automatically.",
        target: "Language to translate the source text into.",
        protection: "Preserve quotes and backticks. Text inside parentheses in quotes is translated.",
        text: "Enter the source text. Queue translates automatically; Translate previews the result before running.",
        button: "Preview the translation before running the workflow. The result appears below and is saved with the workflow.",
        unclosed: "A protected delimiter is not closed. Check the pairs of quotes and backticks.", limit: "Translate up to 5,000 characters at once. The source text is not truncated.",
        marker: "Google changed a protected-text marker. The result was rejected. Try again.", response: "Google returned an invalid or empty translation. Try again.", connection: "Could not connect to Google Translate. Try again later.",
    },
    ko: {
        backend: "번역 엔진입니다. Local OPUS-MT는 CPU로 한국어→영어를 번역합니다.",
        local_language: "로컬 모델은 한국어→영어만 지원합니다. 한국어 또는 자동 감지 → 영어로 선택해 주세요.",
        local_setup: "로컬 CPU 모델 또는 실행 라이브러리가 없습니다. 설치 상태를 확인해 주세요.",
        local_output: "로컬 모델이 번역을 완료하지 못했습니다. 문장을 짧게 나누어 주세요.",
        limited: "번역 · 요청 제한", rate_limit: "구글 번역이 일시적으로 요청을 거절했습니다(HTTP 429). 잠시 기다린 후 다시 시도해 주세요. 제한 해제 시간은 알 수 없습니다.",
        translate: "번역", busy: "번역 중…", done: "번역 · 완료", changed: "번역 · 변경됨", error: "번역 · 오류 (재시도)",
        placeholder: "번역 결과입니다. Queue에서 자동 번역하며, 번역 버튼으로 미리 확인할 수 있습니다.",
        readonly: "읽기 전용 번역 결과입니다.", auto: "자동 감지",
        source: "원문의 언어입니다. 자동 감지를 선택하면 언어를 자동으로 판별합니다.",
        target: "원문을 번역할 도착 언어입니다.",
        protection: "큰따옴표와 백틱 안의 문구를 보존합니다. 큰따옴표 안의 소괄호 내용은 번역합니다.",
        text: "원문을 입력해 주세요. Queue에서 자동 번역하며, 번역 버튼으로 실행 전에 결과를 미리 확인할 수 있습니다.",
        button: "워크플로 실행 전에 번역 결과를 미리 확인합니다. 결과는 아래에 표시되며 워크플로와 함께 저장됩니다.",
        unclosed: "보존 구분자가 닫히지 않았습니다. 따옴표와 백틱의 짝을 확인해 주세요.", limit: "한 번에 최대 5,000자까지 번역할 수 있습니다. 원문은 잘리지 않습니다.",
        marker: "구글 번역이 보존 표시를 변경하여 결과를 적용하지 않았습니다. 다시 시도해 주세요.", response: "구글 번역에서 올바른 결과를 반환하지 않았습니다. 다시 시도해 주세요.", connection: "구글 번역에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
    },
    ja: {
        backend: "翻訳エンジンです。Local OPUS-MTはCPUで韓国語から英語に翻訳します。",
        local_language: "ローカルモデルは韓国語から英語のみ対応しています。韓国語または自動検出 → 英語を選択してください。",
        local_setup: "ローカルCPUモデルまたはライブラリがありません。インストールを確認してください。",
        local_output: "ローカルモデルが翻訳を完了できませんでした。短い文に分割してください。",
        limited: "翻訳 · リクエスト制限", rate_limit: "Google翻訳が一時的にリクエストを拒否しました（HTTP 429）。しばらく待ってから再試行してください。制限の解除時刻は不明です。",
        translate: "翻訳", busy: "翻訳中…", done: "翻訳 · 完了", changed: "翻訳 · 変更あり", error: "翻訳 · エラー（再試行）",
        placeholder: "翻訳結果です。Queueで自動翻訳し、翻訳ボタンでプレビューできます。",
        readonly: "読み取り専用の翻訳結果です。", auto: "自動検出",
        source: "原文の言語です。自動検出を選択すると言語を自動的に判別します。",
        target: "原文の翻訳先言語です。",
        protection: "引用符とバッククォート内の文章を保持します。引用符内の丸括弧の中は翻訳します。",
        text: "原文を入力してください。Queueで自動翻訳し、翻訳ボタンで実行前に確認できます。",
        button: "実行前に翻訳結果をプレビューします。結果は下に表示され、ワークフローと一緒に保存されます。",
        unclosed: "区切り記号が閉じられていません。引用符とバッククォートの組を確認してください。", limit: "一度に翻訳できるのは5,000文字までです。原文は切り詰めません。",
        marker: "保護用の印が変更されたため結果を適用しませんでした。再試行してください。", response: "正しい翻訳結果が返されませんでした。再試行してください。", connection: "Google翻訳に接続できませんでした。後でもう一度お試しください。",
    },
    zh: {
        backend: "翻译引擎。Local OPUS-MT仅使用CPU将韩语翻译为英语。",
        local_language: "本地模型仅支持韩语到英语。请选择韩语或自动检测 → 英语。",
        local_setup: "缺少本地CPU模型或依赖库。请检查安装。",
        local_output: "本地模型未能完成翻译。请将文本拆分成较短的句子。",
        limited: "翻译 · 请求受限", rate_limit: "Google翻译暂时拒绝了请求（HTTP 429）。请等待一段时间后重试。限制解除时间未知。",
        translate: "翻译", busy: "翻译中…", done: "翻译 · 完成", changed: "翻译 · 已更改", error: "翻译 · 错误（重试）",
        placeholder: "翻译结果。Queue自动翻译，翻译按钮用于预览。",
        readonly: "只读翻译结果。", auto: "自动检测",
        source: "原文语言。选择自动检测可自动识别语言。", target: "原文的目标语言。",
        protection: "保留引号和反引号内的文字。引号内圆括号中的内容会翻译。",
        text: "请输入原文。Queue自动翻译，翻译按钮可在运行前预览结果。",
        button: "运行工作流前预览翻译结果。结果显示在下方，并随工作流保存。",
        unclosed: "保护分隔符未闭合。请检查引号和反引号是否成对。", limit: "每次最多翻译5,000个字符。原文不会被截断。",
        marker: "保护标记被更改，因此未应用翻译结果。请重试。", response: "未返回有效翻译结果。请重试。", connection: "无法连接到Google翻译。请稍后重试。",
    },
};

export function locale(app) {
    const value = app.ui?.settings?.getSettingValue?.("Comfy.Locale") || "en";
    const language = String(value).split(/[-_]/)[0].toLowerCase();
    return Object.hasOwn(messages, language) ? language : "en";
}

export function languageLabel(value, app) {
    const code = /\[([^\]]+)\]$/.exec(String(value))?.[1] || String(value);
    if (code === "auto") return `${messages[locale(app)].auto} [auto]`;
    try {
        return `${new Intl.DisplayNames([locale(app)], {type: "language"}).of(code)} [${code}]`;
    } catch {
        return String(value);
    }
}
