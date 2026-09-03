import { test, expect } from '@playwright/test';

test('diagnose fetch to backend', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Test localhost:8000
  const result1 = await page.evaluate(async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/health");
      return { ok: res.ok, status: res.status, text: await res.text() };
    } catch (e) {
      return { error: e.message, name: e.name };
    }
  });
  console.log("Fetch localhost:8000:", result1);

  // Test 127.0.0.1:8000
  const result2 = await page.evaluate(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/health");
      return { ok: res.ok, status: res.status, text: await res.text() };
    } catch (e) {
      return { error: e.message, name: e.name };
    }
  });
  console.log("Fetch 127.0.0.1:8000:", result2);
});
