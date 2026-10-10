import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/editor/editor.api.js";
import { conf, language } from "monaco-editor/languages/definitions/cpp/cpp.js";
import EditorWorker from "monaco-editor/editor/editor.worker.js?worker";

// Bundle the editor, C++ tokenizer and worker locally. No CDN is required.
Object.assign(globalThis, {
  MonacoEnvironment: { getWorker: () => new EditorWorker() },
});
loader.config({ monaco });
// Register eagerly so Vite's dependency optimization cannot invalidate a lazy
// tokenizer URL while an editor is starting.
monaco.languages.register({
  id: "cpp",
  extensions: [".cpp", ".cc", ".cxx", ".hpp", ".h"],
  aliases: ["C++", "cpp"],
});
monaco.languages.setLanguageConfiguration("cpp", conf);
monaco.languages.setMonarchTokensProvider("cpp", language);
