import { expect, test } from "@playwright/test";

test("happy path: Jacket A skip, Jacket B worth it, methodology, fallback control", async ({
  page,
}) => {
  await page.goto("/demo");
  await expect(page.getByRole("heading", { name: "WorthWearing" })).toBeVisible();

  await page.getByRole("radio", { name: /jacket a/i }).click();
  await page.getByTestId("try-with-wardrobe").click();
  await expect(page.getByTestId("analysis-progress")).toBeVisible();
  await expect(page.getByTestId("recommendation-badge")).toContainText("Skip It", {
    timeout: 20_000,
  });
  await expect(page.getByTestId("tryon-image")).toBeVisible();
  await page.getByTestId("why-this-result").click();
  await expect(page.getByTestId("methodology-panel")).toBeVisible();
  await expect(page.getByTestId("factor-breakdown")).toContainText("Duplication");

  await page.getByRole("radio", { name: /jacket b/i }).click();
  await page.getByTestId("try-with-wardrobe").click();
  await expect(page.getByTestId("recommendation-badge")).toContainText("Worth It", {
    timeout: 20_000,
  });
  await expect(page.getByTestId("comparison")).toBeVisible();
  await expect(page.getByTestId("outfit-carousel")).toBeVisible();
  await expect(page.getByTestId("provider-badge")).toContainText(/Prepared demo|Live API/);

  await expect(page.getByTestId("retailer-value")).toContainText(
    "We don’t help shoppers buy more"
  );

  await page.route("**/api/try-on", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: "live-timeout",
          status: "failed",
          provider: "live",
          prepared_fallback_available: true,
          prepared_fallback_url: "/assets/jacket-b-tryon.png",
          error_category: "timeout",
          error_message: "Live try-on timed out.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.route("**/api/try-on/*/fallback", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "live-timeout",
        status: "completed",
        provider: "demo",
        result_image_url: "/assets/jacket-b-tryon.png",
        prepared_fallback_available: true,
        prepared_fallback_url: "/assets/jacket-b-tryon.png",
      }),
    });
  });

  await page.getByTestId("try-with-wardrobe").click();
  await expect(page.getByTestId("use-prepared-demo")).toBeVisible();
  await page.getByTestId("use-prepared-demo").click();
  await expect(page.getByTestId("provider-badge")).toContainText("Prepared demo");
});
