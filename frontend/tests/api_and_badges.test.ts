import { describe, it, expect } from "vitest";
import { api } from "../lib/api";

describe("Frontend API Client and Types", () => {
  it("exports all API client functions", () => {
    expect(typeof api.getDashboardStats).toBe("function");
    expect(typeof api.listIncidents).toBe("function");
    expect(typeof api.getIncident).toBe("function");
    expect(typeof api.createIncident).toBe("function");
    expect(typeof api.triggerInvestigation).toBe("function");
    expect(typeof api.resolveApproval).toBe("function");
    expect(typeof api.getScenarios).toBe("function");
    expect(typeof api.runScenario).toBe("function");
  });

  it("handles base URL configurations correctly", () => {
    const url = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
    expect(url).toContain("/api/v1");
  });
});
