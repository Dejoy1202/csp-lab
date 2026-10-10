import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
const edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const executablePath =
  process.env.CSP_BROWSER_PATH || (existsSync(edge) ? edge : undefined);
export default defineConfig({
  testDir: "./tests",
  timeout: 120000,
  expect: { timeout: 15000 },
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [
    ["list"],
    ["json", { outputFile: "../test-results/playwright/results.json" }],
    [
      "html",
      { outputFolder: "../test-results/playwright/report", open: "never" },
    ],
  ],
  outputDir: "../test-results/playwright/artifacts",
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    permissions: ["clipboard-read", "clipboard-write"],
    viewport: { width: 1440, height: 900 },
    launchOptions: { executablePath },
    trace: "off",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --strictPort",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
    timeout: 30000,
  },
});
