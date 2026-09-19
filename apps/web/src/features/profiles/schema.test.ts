import { describe, expect, it } from "vitest";
import { BIO_MAX, profileFormSchema, toPayload } from "./schema";

const valid = { name: "Asha Rao", branch: "Mathematics and Computing", year: "3", bio: "" };

describe("profileFormSchema", () => {
  it("accepts a complete profile", () => {
    expect(profileFormSchema.safeParse(valid).success).toBe(true);
  });

  it.each([
    ["blank name", { name: "   " }],
    ["name too long", { name: "n".repeat(101) }],
    ["no branch", { branch: "" }],
    ["year 0", { year: "0" }],
    ["year 6", { year: "6" }],
    ["non-numeric year", { year: "third" }],
    ["bio too long", { bio: "b".repeat(BIO_MAX + 1) }],
  ])("rejects %s", (_label, override) => {
    expect(profileFormSchema.safeParse({ ...valid, ...override }).success).toBe(false);
  });
});

describe("toPayload", () => {
  it("converts year to a number and trims the name", () => {
    expect(toPayload({ ...valid, name: "  Asha  " })).toEqual({
      name: "Asha",
      branch: "Mathematics and Computing",
      year: 3,
      bio: null,
    });
  });

  it("sends null for a blank bio so the API clears it", () => {
    expect(toPayload({ ...valid, bio: "   " }).bio).toBeNull();
    expect(toPayload({ ...valid, bio: "hello" }).bio).toBe("hello");
  });
});
