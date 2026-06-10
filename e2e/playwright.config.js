// Assumes backend (:8000, MOCK_LLM=1) and frontend (:3000) are running -
// `make e2e` / CI orchestrate that. Keep this config dumb on purpose.
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: ".",
  timeout: 30000,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    headless: true,
  },
});
