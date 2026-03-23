import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AIChat from "../AIChat";

const AI_RESULT = {
  query: "Show me all UPS routes",
  sql: "SELECT * FROM routes WHERE carrier = 'UPS'",
  results: [
    { carrier_name: "UPS", origin: "Dallas", destination: "Houston" },
  ],
  explanation: "This query finds all routes operated by UPS.",
};

describe("AIChat", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders input, submit button, and suggestion chips", () => {
    render(<AIChat />);

    expect(
      screen.getByPlaceholderText(/Ask about freight movements/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask" })).toBeInTheDocument();

    // Check suggestion chips are rendered
    expect(
      screen.getByText("Which carriers operate between New York and Washington DC?")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Top carriers from San Francisco to Los Angeles")
    ).toBeInTheDocument();
  });

  it("disables Ask button when input is empty", () => {
    render(<AIChat />);
    expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();
  });

  it("submits query on form submit", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => AI_RESULT,
      } as Response);

    const user = userEvent.setup();
    render(<AIChat />);

    const input = screen.getByPlaceholderText(/Ask about freight movements/i);
    await user.type(input, "Show me all UPS routes");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8000/ai-query",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "Show me all UPS routes" }),
      })
    );
  });

  it("submits query when clicking a suggestion chip", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => AI_RESULT,
      } as Response);

    const user = userEvent.setup();
    render(<AIChat />);

    await user.click(screen.getByText("Show me all UPS routes"));

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8000/ai-query",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "Show me all UPS routes" }),
      })
    );
  });

  it("shows loading state while fetching", async () => {
    let resolveFetch!: (value: Response) => void;
    vi.spyOn(globalThis, "fetch").mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );

    const user = userEvent.setup();
    render(<AIChat />);

    await user.type(screen.getByPlaceholderText(/Ask about freight/i), "test query");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(screen.getByText("Processing your query...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Thinking..." })).toBeDisabled();

    resolveFetch({
      ok: true,
      json: async () => AI_RESULT,
    } as Response);

    await waitFor(() => {
      expect(screen.queryByText("Processing your query...")).not.toBeInTheDocument();
    });
  });

  it("displays error message on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network error"));

    const user = userEvent.setup();
    render(<AIChat />);

    await user.type(screen.getByPlaceholderText(/Ask about freight/i), "bad query");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(
        screen.getByText("Failed to process query. Make sure the API server is running.")
      ).toBeInTheDocument();
    });
  });

  it("displays result with SQL, explanation, and results table", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => AI_RESULT,
    } as Response);

    const user = userEvent.setup();
    render(<AIChat />);

    await user.type(screen.getByPlaceholderText(/Ask about freight/i), "Show me all UPS routes");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByText("Generated SQL")).toBeInTheDocument();
    });

    expect(screen.getByText(AI_RESULT.sql)).toBeInTheDocument();
    expect(screen.getByText("Explanation")).toBeInTheDocument();
    expect(screen.getByText(AI_RESULT.explanation)).toBeInTheDocument();
    expect(screen.getByText("Results (1)")).toBeInTheDocument();
    expect(screen.getByText("UPS")).toBeInTheDocument();
  });
});
