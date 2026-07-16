/** TailAdmin Editor theme — Prism code block presets and CSS helpers */

export const codeBlockShellClass =
  "w-full flex-1 rounded-2xl border border-gray-200 dark:border-gray-800";

export const codeBlockHeaderClass =
  "flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800";

export const codeBlockLanguageLabelClass =
  "flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400";

export const codeBlockToolbarClass = "flex gap-2";

export const codeBlockToolbarButtonClass =
  "inline-flex size-8 items-center justify-center rounded-full border border-gray-200 text-gray-700 dark:border-gray-800 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5";

export const codeBlockBodyClass =
  "py-4 px-5 max-h-[350px] w-full overflow-y-auto custom-scrollbar";

export const codeBlockPreClass = "rounded-lg overflow-x-auto p-4 text-sm";

export const codeBlockPreWithLineNumbersClass = `${codeBlockPreClass} line-numbers`;

/** Languages to lazy-import in host app */
export const prismLanguageImports = [
  "prismjs/components/prism-jsx",
  "prismjs/components/prism-tsx",
  "prismjs/components/prism-typescript",
  "prismjs/components/prism-bash",
  "prismjs/components/prism-json",
  "prismjs/components/prism-css",
  "prismjs/components/prism-scss",
  "prismjs/components/prism-markdown",
] as const;

export type PrismLanguage =
  | "jsx"
  | "tsx"
  | "typescript"
  | "bash"
  | "json"
  | "css"
  | "scss"
  | "markdown"
  | "html";

export const supportedPrismLanguages: PrismLanguage[] = [
  "jsx",
  "tsx",
  "typescript",
  "bash",
  "json",
  "css",
  "scss",
  "markdown",
  "html",
];

/** Build code element className for Prism */
export function getPrismLanguageClass(language: PrismLanguage): string {
  return `language-${language}`;
}

/** Global Prism CSS overrides for host index.css */
export const prismCssOverrides = `
code[class*="language-"],
pre[class*="language-"] {
  text-shadow: none;
  color: #344054;
  overflow: hidden !important;
  font-size: 14px;
  margin: 0;
  padding: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  text-align: justify;
}
.dark code[class*="language-"],
.dark pre[class*="language-"] {
  text-shadow: none;
  color: #98a2b3;
}
[data-theme="light"] .language-html {
  background-color: #ffffff !important;
}
[data-theme="dark"] .language-html {
  background-color: #171f2e !important;
}
.token {
  text-shadow: none;
  font-size: 14px;
}
.token.doctype-tag,
.token.name {
  color: #018001;
}
.token.tag,
.token.selector {
  color: #267f99;
}
.token.property {
  color: #0070c1;
}
.token.language-css {
  color: #1b00ff;
}
.token.attr-name {
  color: #98a2b3;
}
.token.attr-value {
  color: #a31615;
}
.token.punctuation {
  color: #344054;
}
.dark .token.punctuation {
  color: #98a2b3;
}
.line-numbers .line-numbers-rows {
  border-right: 0 !important;
}
pre[class*="language-"].line-numbers {
  padding-left: 2.8em !important;
}
` as const;
