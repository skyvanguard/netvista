/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional API key sent with every request when the backend requires auth. */
  readonly VITE_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
