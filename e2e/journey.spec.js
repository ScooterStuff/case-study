// The one e2e test: the full fix-it journey against the MOCK_LLM backend.
// symptom -> diagnosis block -> check a part fits a model -> verdict block ->
// add to cart -> badge increments.
const { test, expect } = require("@playwright/test");

test("fix-it journey: diagnose -> compatibility -> cart", async ({ page }) => {
  await page.goto("/");

  // 1. symptom -> diagnosis card with ranked causes + suggested parts
  const box = page.getByLabel("Message");
  await box.fill("The ice maker on my Whirlpool fridge is not working. How can I fix it?");
  await box.press("Enter");
  const diagnosis = page.locator(".diagnosis");
  await expect(diagnosis).toBeVisible({ timeout: 15000 });
  await expect(diagnosis.locator(".cause-rank").first()).toHaveText("1");
  const firstPart = diagnosis.locator(".product-card").first();
  await expect(firstPart).toBeVisible();

  // 2. chat-native compatibility check from the product card
  await firstPart.getByRole("button", { name: "Check fits my model" }).click();
  await firstPart.getByLabel("Model number").fill("WDT780SAEM1");
  await firstPart.getByRole("button", { name: "Check" }).click();
  const verdict = page.locator(".compat").last();
  await expect(verdict).toBeVisible({ timeout: 15000 });
  await expect(verdict.locator(".compat-title")).not.toBeEmpty();

  // 3. add to cart -> badge increments, drawer shows the line item
  await page.locator(".product-card").first().getByRole("button", { name: "Add to cart" }).click();
  await expect(page.locator(".cart-badge")).toHaveText("1");
  await expect(page.locator(".drawer .cart-line")).toHaveCount(1);

  // 4. off-topic question renders a graceful deflection (no broken blocks)
  await page.locator(".drawer-overlay").click({ position: { x: 10, y: 10 } });
  await box.fill("What is the capital of France?");
  await box.press("Enter");
  await expect(page.locator(".msg.assistant").last()).toContainText(/parts|fridge|dishwasher/i,
    { timeout: 15000 });
});
