/// <reference types="vite/client" />
declare module "monaco-editor/languages/definitions/cpp/cpp.js" {
  import type { languages } from "monaco-editor";
  export const conf: languages.LanguageConfiguration;
  export const language: languages.IMonarchLanguage;
}
