import js from '/opt/quality/node_modules/@eslint/js/src/index.js';
import security from '/opt/quality/node_modules/eslint-plugin-security/index.js';

export default [
  {
    ignores: ['**/node_modules/**', '.soulkiller-local/**', '.git/**'],
  },
  {
    files: ['tools/**/*.mjs', 'eslint.config.mjs'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        AbortController: 'readonly',
        AbortSignal: 'readonly',
        Response: 'readonly',
        TextDecoder: 'readonly',
        Buffer: 'readonly',
        URL: 'readonly',
        clearTimeout: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        process: 'readonly',
        setTimeout: 'readonly',
        structuredClone: 'readonly',
      },
    },
    plugins: { security },
    rules: {
      ...js.configs.recommended.rules,
      ...security.configs.recommended.rules,
    },
  },
];
