import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  use: {
    baseURL: process.env.WEB_BASE_URL || "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1050 },
      },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
    ...(process.env.REFILENS_WEBKIT === "1"
      ? [
          {
            name: "webkit",
            use: {
              ...devices["Desktop Safari"],
              browserName: "webkit" as const,
              viewport: { width: 1440, height: 1050 },
            },
          },
        ]
      : []),
  ],
});
