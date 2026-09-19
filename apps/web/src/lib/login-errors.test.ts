import { describe, expect, it } from "vitest";
import { loginErrorMessage } from "./login-errors";

describe("loginErrorMessage", () => {
  it("returns null when there is no error", () => {
    expect(loginErrorMessage(undefined)).toBeNull();
    expect(loginErrorMessage("")).toBeNull();
  });

  it.each([
    "domain_not_allowed",
    "email_not_verified",
    "cancelled",
    "oauth_failed",
    "not_configured",
    "account_disabled",
    "account_conflict",
  ])("has a specific message for %s", (code) => {
    const msg = loginErrorMessage(code);
    expect(msg).toBeTruthy();
    expect(msg).not.toMatch(/something went wrong/i);
  });

  it("falls back to a generic message for unknown codes (and never echoes the code)", () => {
    const msg = loginErrorMessage("<script>alert(1)</script>");
    expect(msg).toMatch(/something went wrong/i);
    expect(msg).not.toContain("script");
  });
});
