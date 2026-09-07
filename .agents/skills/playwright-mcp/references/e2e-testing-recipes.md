# Playwright MCP: E2E Testing Recipes & Workflow Patterns

Các kịch bản mẫu kiểm thử luồng người dùng (User Flows) thông dụng bằng Playwright và Playwright MCP.

---

## 1. Kịch Bản 1: Kiểm Thử Đăng Nhập (Authentication Flow)

```typescript
import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("đăng nhập thành công và chuyển hướng về dashboard", async ({ page }) => {
    // 1. Mở trang đăng nhập
    await page.goto("/login");

    // 2. Điền thông tin đăng nhập
    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Mật khẩu").fill("Secret123!");

    // 3. Nhấn nút Đăng nhập
    await page.getByRole("button", { name: "Đăng nhập" }).click();

    // 4. Kỳ vọng chuyển hướng và hiển thị lời chào
    await expect(page).toHaveURL("/dashboard");
    await expect(page.getByText("Xin chào,")).toBeVisible();
  });

  test("hiển thị thông báo lỗi khi sai mật khẩu", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Mật khẩu").fill("WrongPassword");
    await page.getByRole("button", { name: "Đăng nhập" }).click();

    await expect(page.getByRole("alert")).toContainText("Thông tin đăng nhập không chính xác");
  });
});
```

---

## 2. Kịch Bản 2: Kiểm Thử Đặt Hàng & Giỏ Hàng (Cart & Checkout Flow)

```typescript
import { test, expect } from "@playwright/test";

test("thêm sản phẩm vào giỏ hàng và thanh toán", async ({ page }) => {
  await page.goto("/products/laptop-pro");

  // Thêm vào giỏ
  await page.getByRole("button", { name: "Thêm vào giỏ" }).click();

  // Mở drawer giỏ hàng
  await expect(page.getByText("Sản phẩm đã được thêm")).toBeVisible();
  await page.getByRole("link", { name: "Giỏ hàng" }).click();

  // Kiểm tra số lượng & tổng tiền
  await expect(page.getByTestId("cart-item-count")).toHaveText("1");
  
  // Bấm tiến hành thanh toán
  await page.getByRole("button", { name: "Thanh toán" }).click();
  await expect(page).toHaveURL(/\/checkout/);
});
```

---

## 3. Kịch Bản 3: Kiểm Thử Trực Quan (Visual Regression Test)

```typescript
import { test, expect } from "@playwright/test";

test("giao diện trang chủ không bị vỡ layout", async ({ page }) => {
  await page.goto("/");
  
  // Chờ tất cả font chữ và ảnh tải xong
  await page.waitForLoadState("networkidle");

  // So khớp ảnh chụp màn hình với baseline chuẩn
  await expect(page).toHaveScreenshot("homepage-baseline.png", {
    maxDiffPixels: 100,
  });
});
```
