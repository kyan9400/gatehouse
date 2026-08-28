import { describe, expect, it } from "vitest";

import { demoData } from "./data";

describe("demo data", () => {
  it("contains a reviewable high-risk request", () => {
    expect(demoData.requests.some((request) => request.status === "pending" && request.risk === "high")).toBe(true);
  });
});
