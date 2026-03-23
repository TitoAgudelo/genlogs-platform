import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Home from "../page";

describe("Home page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Default mock for any fetch calls
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);
  });

  it("renders Route Search tab as active by default", () => {
    render(<Home />);

    const searchTab = screen.getByRole("button", { name: "Route Search" });
    const aiTab = screen.getByRole("button", { name: "AI Assistant" });

    expect(searchTab).toHaveClass("active");
    expect(aiTab).not.toHaveClass("active");
  });

  it("shows SearchForm and CarrierList in search tab", () => {
    render(<Home />);

    expect(screen.getByLabelText("From (City)")).toBeInTheDocument();
    expect(
      screen.getByText("Select origin and destination cities to find carriers on this route.")
    ).toBeInTheDocument();
  });

  it("switches to AI Assistant tab", async () => {
    render(<Home />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "AI Assistant" }));

    expect(screen.getByRole("button", { name: "AI Assistant" })).toHaveClass("active");
    expect(screen.getByRole("button", { name: "Route Search" })).not.toHaveClass("active");

    // AI chat input should be visible
    expect(screen.getByPlaceholderText(/Ask about freight movements/i)).toBeInTheDocument();

    // Search form should not be visible
    expect(screen.queryByLabelText("From (City)")).not.toBeInTheDocument();
  });

  it("switches back from AI to Search tab", async () => {
    render(<Home />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "AI Assistant" }));
    await user.click(screen.getByRole("button", { name: "Route Search" }));

    expect(screen.getByRole("button", { name: "Route Search" })).toHaveClass("active");
    expect(screen.getByLabelText("From (City)")).toBeInTheDocument();
  });

  it("performs search and displays results", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
      const urlStr = typeof url === "string" ? url : url.toString();
      if (urlStr.includes("/search")) {
        return {
          ok: true,
          json: async () => ({
            origin: "Dallas",
            destination: "Houston",
            carriers: [{ carrier_name: "UPS Inc.", trucks_per_day: 11 }],
            total_carriers: 1,
          }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const user = userEvent.setup();
    render(<Home />);

    await user.type(screen.getByLabelText("From (City)"), "Dallas");
    await user.type(screen.getByLabelText("To (City)"), "Houston");
    await user.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => {
      expect(screen.getByText("UPS Inc.")).toBeInTheDocument();
    });
    expect(screen.getByText("1 carrier found")).toBeInTheDocument();
  });
});
