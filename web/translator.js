import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { messages, locale, languageLabel } from "./i18n.js";

app.registerExtension({
    name: "cozdx1.GoogleTranslatePlus",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "GoogleTranslatePlus") return;
        const created = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const previous = created?.apply(this, arguments);
            const find = (name) => this.widgets.find((widget) => widget.name === name);
            const source = find("text"), output = find("translated_text"), state = find("translation_state");
            // Also apply the new default when an older backend is still running.
            const sourceLanguage = find("source_language");
            const autoValue = sourceLanguage.options?.values?.find?.((value) => /\[auto\]$/.test(value));
            if (autoValue) sourceLanguage.value = autoValue;
            for (const name of ["source_language", "target_language"]) {
                const widget = find(name), originalClick = widget.onClick;
                if (typeof originalClick !== "function") continue;
                widget.onClick = function (context) {
                    const {e, node, canvas} = context;
                    const x = e.canvasX - node.pos[0], width = this.width || node.size[0];
                    const ContextMenu = globalThis.LiteGraph?.ContextMenu;
                    if (x < 40 || x > width - 40 || !ContextMenu) return originalClick.call(this, context);
                    const choices = this.options.values.map((value) => ({content: languageLabel(value, app), value}));
                    // Provide all entries at construction so ComfyUI's native
                    // ContextMenuFilter adds its search field and keyboard controls.
                    return new ContextMenu(choices, {
                        event: e, className: "dark", scale: Math.max(1, canvas.ds.scale),
                        callback: (choice) => this.setValue(choice.value, context),
                    });
                };
            }
            const watched = ["text", "source_language", "target_language", "protection"];
            const snapshot = () => Object.fromEntries(watched.map((name) => [name, find(name).value]));
            let observedInput = JSON.stringify(snapshot());
            let status = "translate";
            const strings = () => messages[locale(app)];
            const lockOutput = () => {
                if (output.inputEl) {
                    output.inputEl.readOnly = true;
                    output.inputEl.placeholder = strings().placeholder;
                    output.inputEl.title = strings().readonly;
                    output.inputEl.setAttribute("aria-label", strings().readonly);
                }
            };
            // Keep the state in workflow serialization, but do not draw a control for it.
            state.type = "hidden";
            state.computeSize = () => [0, -4];
            state.draw = () => {};
            const button = this.addWidget("button", "Translate", null, async () => {
                if (this._googleTranslateBusy) return;
                this._googleTranslateBusy = true;
                status = "busy";
                button.name = strings()[status];
                const input = snapshot();
                state.value = "";
                this.setDirtyCanvas(true, true);
                try {
                    const response = await api.fetchApi("/cozdx1/google-translate-plus/translate", {
                        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input),
                    });
                    const data = await response.json();
                    if (!response.ok) throw new Error(strings()[data.code] || data.error || `HTTP ${response.status}`);
                    if (JSON.stringify(input) !== JSON.stringify(snapshot())) {
                        status = "changed";
                        button.name = strings()[status];
                        return;
                    }
                    output.value = data.text;
                    state.value = data.state;
                    observedInput = JSON.stringify(input);
                    this._googleTranslateError = "";
                    status = "done";
                    button.name = strings()[status];
                } catch (error) {
                    this._googleTranslateError = String(error.message || error);
                    status = "error";
                    button.name = strings()[status];
                    app.extensionManager?.toast?.add({severity: "error", summary: "Google Translate Plus", detail: this._googleTranslateError, life: 12000});
                    console.warn("Google Translate Plus:", this._googleTranslateError);
                } finally {
                    this._googleTranslateBusy = false;
                    lockOutput();
                    this.setDirtyCanvas(true, true);
                }
            }, { serialize: false });
            for (const name of watched) {
                const widget = find(name), callback = widget.callback;
                widget.callback = (...args) => {
                    const result = callback?.apply(widget, args);
                    // ComfyUI may assign the same value during export/queue/configure.
                    // A callback alone is not evidence that the input changed.
                    const currentInput = JSON.stringify(snapshot());
                    if (currentInput !== observedInput) {
                        observedInput = currentInput;
                        state.value = "";
                        status = "changed";
                        button.name = strings()[status];
                        this.setDirtyCanvas(true, true);
                    }
                    return result;
                };
            }
            // Button immediately before source text; translated text remains directly below it.
            this.widgets.splice(this.widgets.indexOf(button), 1);
            this.widgets.splice(this.widgets.indexOf(source), 0, button);
            const localize = () => {
                lockOutput();
                button.name = strings()[status];
                button.options.tooltip = strings().button;
                button.tooltip = strings().button;
                for (const [name, key] of [["source_language", "source"], ["target_language", "target"], ["protection", "protection"], ["text", "text"], ["translated_text", "readonly"]]) {
                    const widget = find(name);
                    widget.options ??= {};
                    widget.options.tooltip = strings()[key];
                    widget.tooltip = strings()[key];
                    if (widget.inputEl) widget.inputEl.title = strings()[key];
                }
                for (const name of ["source_language", "target_language"]) {
                    const widget = find(name);
                    widget.options.getOptionLabel = (value) => languageLabel(value, app);
                    if (Array.isArray(widget.options.values)) {
                        const collator = new Intl.Collator(locale(app), {sensitivity: "base"});
                        widget.options.values = [...widget.options.values].sort((a, b) => {
                            const autoA = /\[auto\]$/.test(a), autoB = /\[auto\]$/.test(b);
                            if (autoA !== autoB) return autoA ? -1 : 1;
                            return collator.compare(languageLabel(a, app), languageLabel(b, app));
                        });
                    }
                }
                this.setDirtyCanvas(true, true);
            };
            localize();
            const executed = this.onExecuted;
            this.onExecuted = function (data) {
                const previousResult = executed?.apply(this, arguments);
                const input = data?.input_snapshot?.[0];
                if (input && JSON.stringify(input) === JSON.stringify(snapshot()) && typeof data.translated_text?.[0] === "string") {
                    output.value = data.translated_text[0];
                    state.value = data.translation_state[0];
                    observedInput = JSON.stringify(input);
                    status = "done";
                    this._googleTranslateError = "";
                    localize();
                }
                return previousResult;
            };
            app.ui?.settings?.addEventListener?.("Comfy.Locale.change", localize);
            const removed = this.onRemoved;
            this.onRemoved = function () {
                app.ui?.settings?.removeEventListener?.("Comfy.Locale.change", localize);
                return removed?.apply(this, arguments);
            };
            const configure = this.onConfigure;
            this.onConfigure = function () {
                const result = configure?.apply(this, arguments);
                observedInput = JSON.stringify(snapshot());
                localize();
                return result;
            };
            this.setSize([500, 560]);
            return previous;
        };
    },
});
