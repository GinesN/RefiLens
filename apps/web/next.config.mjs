import path from "node:path";
try {
  process.loadEnvFile(path.resolve(import.meta.dirname, "../../.env"));
} catch {
  /* .env is optional */
}

/** @type {import('next').NextConfig} */
const config = { poweredByHeader: false, devIndicators: false };
export default config;
