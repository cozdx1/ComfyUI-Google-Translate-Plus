const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
let extension;
let requestCount = 0;
let resolveRequest;
let response;
let uiLocale = 'en';
let openedMenu;
const settingListeners = new Map();
const context = {
    app: {registerExtension: (value) => { extension = value; }, extensionManager: {toast: {add: () => {}}}, ui: {settings: {
        getSettingValue: () => uiLocale,
        addEventListener: (name, callback) => settingListeners.set(name, callback),
        removeEventListener: (name) => settingListeners.delete(name),
    }}},
    api: {fetchApi: () => { requestCount++; return response || new Promise((resolve) => { resolveRequest = resolve; }); }},
    console: {warn: () => {}},
    LiteGraph: {ContextMenu: class {constructor(values, options) {openedMenu = {values, options};}}},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/i18n.js'), 'utf8').replace(/^export /gm, ''), context);
const source = fs.readFileSync(path.join(__dirname, '../web/translator.js'), 'utf8').replace(/^import .*;\s*$/gm, '');
vm.runInContext(source, context);
class Node {
    constructor() {
        this.widgets = ['source_language', 'target_language', 'protection', 'text', 'translated_text', 'translation_state'].map((name) => ({
            name, value: name === 'text' ? 'original' : '', inputEl: name === 'translated_text' ? {setAttribute: () => {}} : undefined,
            options: ['source_language', 'target_language'].includes(name) ? {values:[
                ...(name === 'source_language' ? ['자동 감지 [auto]'] : []),
                '갈리시아어 [gl]', '광둥어 [yue]', '덴마크어 [da]', '독일어 [de]', '한국어 [ko]',
            ]} : {},
            onClick() { this.defaultClick = true; },
            setValue(value) { this.value = value; this.callback?.(value); },
        }));
    }
    addWidget(type, name, value, callback, options) {
        const widget = {type, name, value, callback, options};
        this.widgets.push(widget);
        return widget;
    }
    setSize() {}
    setDirtyCanvas() {}
}
(async () => {
    await extension.beforeRegisterNodeDef(Node, {name: 'GoogleTranslatePlus'});
    const node = new Node();
    node.onNodeCreated();
    const widget = (name) => node.widgets.find((value) => value.name === name);
    const button = node.widgets.find((value) => value.type === 'button');
    const output = widget('translated_text'), state = widget('translation_state');
    assert.equal(output.inputEl.readOnly, true);
    assert.equal(widget('source_language').value, '자동 감지 [auto]', 'new nodes default to auto-detect');
    assert.equal(widget('source_language').options.getOptionLabel('자동 감지 [auto]'), 'Auto-detect [auto]');
    assert.equal(widget('target_language').options.getOptionLabel('영어 [en]'), 'English [en]');
    assert.deepEqual(Array.from(widget('source_language').options.values, (value) => widget('source_language').options.getOptionLabel(value)),
        ['Auto-detect [auto]', 'Cantonese [yue]', 'Danish [da]', 'Galician [gl]', 'German [de]', 'Korean [ko]'],
        'language menus must sort by displayed names, not underlying Korean labels');
    const clickContext = {e: {canvasX: 250}, node: {pos: [0, 0], size: [500, 560]}, canvas: {ds: {scale: 1}}};
    for (const name of ['source_language', 'target_language']) {
        widget(name).onClick(clickContext);
        assert.equal(openedMenu.options.className, 'dark');
        assert.ok(openedMenu.values.length > 4, 'native filtering needs the full menu at construction');
        assert.ok(openedMenu.values.some((choice) => choice.content === 'Korean [ko]'));
        const savedValue = widget(name).value;
        openedMenu.options.callback(openedMenu.values.find((choice) => choice.value === '한국어 [ko]'));
        assert.equal(widget(name).value, '한국어 [ko]', 'filtered selections keep backend language values');
        widget(name).value = savedValue;
        widget(name).onClick({...clickContext, e: {canvasX: 20}});
        assert.equal(widget(name).defaultClick, true, 'arrow buttons keep the native combo behavior');
    }
    assert.ok(output.inputEl.placeholder.endsWith('.'));
    assert.equal(state.type, 'hidden');
    assert.equal(button.options.serialize, false);
    const first = button.callback();
    await button.callback();
    assert.equal(requestCount, 1, 'double clicks must not send multiple requests');
    widget('text').value = 'changed';
    resolveRequest({ok: true, json: async () => ({text: 'stale translation', state: 'old'})});
    await first;
    assert.equal(output.value, '', 'late response must not overwrite current text');
    assert.equal(state.value, '');
    response = {ok: true, json: async () => ({text: 'fresh translation', state: 'valid'})};
    await button.callback();
    assert.equal(widget('text').value, 'changed', 'source must remain unchanged');
    assert.equal(output.value, 'fresh translation');
    assert.equal(state.value, 'valid');
    widget('text').callback(widget('text').value);
    widget('source_language').callback(widget('source_language').value);
    widget('target_language').callback(widget('target_language').value);
    widget('protection').callback(widget('protection').value);
    assert.equal(state.value, 'valid', 'unchanged callbacks during export/queue must preserve translation state');
    widget('target_language').value = 'different language';
    widget('target_language').callback();
    assert.equal(state.value, '', 'changing the target invalidates the translation');
    response = {ok: false, json: async () => ({error: 'Rate limited'})};
    await button.callback();
    assert.equal(widget('text').value, 'changed');
    assert.equal(state.value, '');
    assert.equal(node._googleTranslateError, 'Rate limited');
    assert.equal(node._googleTranslateBusy, false);
    node.onConfigure();
    assert.equal(output.inputEl.readOnly, true);
    const queueSnapshot = Object.fromEntries(['text', 'source_language', 'target_language', 'protection'].map((name) => [name, widget(name).value]));
    node.onExecuted({input_snapshot: [queueSnapshot], translated_text: ['Queue result'], translation_state: ['queue-state']});
    assert.equal(output.value, 'Queue result', 'Queue result must appear in the inline preview');
    assert.equal(state.value, 'queue-state', 'Queue result must be saved with the workflow');
    widget('text').callback(widget('text').value);
    assert.equal(state.value, 'queue-state', 'unchanged export callbacks must preserve Queue results');
    widget('text').value = 'newer input';
    widget('text').callback();
    node.onExecuted({input_snapshot: [queueSnapshot], translated_text: ['Late Queue result'], translation_state: ['stale-state']});
    assert.equal(output.value, 'Queue result', 'late Queue results must not overwrite newer input');
    assert.equal(state.value, '', 'late Queue results must not validate newer input');
    for (const language of ['ko', 'ja', 'zh-CN', 'en', 'fr']) {
        uiLocale = language;
        settingListeners.get('Comfy.Locale.change')();
        for (const name of ['source_language', 'target_language']) {
            const values = widget(name).options.values.filter((value) => !value.endsWith('[auto]'));
            const collator = new Intl.Collator(['ko', 'ja', 'zh-CN', 'en'].includes(language) ? language : 'en', {sensitivity: 'base'});
            for (let index = 1; index < values.length; index++) {
                assert.ok(collator.compare(widget(name).options.getOptionLabel(values[index - 1]), widget(name).options.getOptionLabel(values[index])) <= 0,
                    'changing the UI locale must sort menus by the new displayed names');
            }
        }
        const translated = output.inputEl.placeholder;
        assert.ok(translated.endsWith('.') || translated.endsWith('。'), 'localized hints must end with punctuation');
        if (language === 'ko') assert.ok(translated.includes('번역 결과'));
        if (language === 'ja') assert.ok(translated.includes('翻訳結果'));
        if (language === 'zh-CN') assert.ok(translated.includes('翻译结果'));
        if (language === 'fr') assert.ok(translated.startsWith('Translation result.'), 'unsupported locales use English');
        assert.equal(widget('text').value, 'newer input', 'changing UI language never changes source text');
    }
    node.onRemoved();
    assert.equal(settingListeners.size, 0, 'removed nodes release locale listeners');
    console.log('Frontend: readonly, manual request, duplicate click, late response, stale state, failure, configure PASS');
})().catch((error) => {console.error(error); process.exitCode = 1;});
