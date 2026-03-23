import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SearchForm from "../SearchForm";

describe("SearchForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders origin and destination inputs and a submit button", () => {
    render(<SearchForm onSearch={vi.fn()} loading={false} />);

    expect(screen.getByLabelText("From (City)")).toBeInTheDocument();
    expect(screen.getByLabelText("To (City)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("renders text inputs with correct placeholders", () => {
    render(<SearchForm onSearch={vi.fn()} loading={false} />);

    expect(screen.getByPlaceholderText("e.g. New York")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Washington DC")).toBeInTheDocument();
  });

  it("calls onSearch with origin and destination on form submission", async () => {
    const onSearch = vi.fn();
    const user = userEvent.setup();
    render(<SearchForm onSearch={onSearch} loading={false} />);

    await user.type(screen.getByLabelText("From (City)"), "Dallas");
    await user.type(screen.getByLabelText("To (City)"), "Houston");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(onSearch).toHaveBeenCalledWith("Dallas", "Houston");
  });

  it("disables button and shows loading text when loading is true", () => {
    render(<SearchForm onSearch={vi.fn()} loading={true} />);

    const button = screen.getByRole("button", { name: "Searching..." });
    expect(button).toBeDisabled();
  });

  it("disables button when no city is entered", () => {
    render(<SearchForm onSearch={vi.fn()} loading={false} />);

    const button = screen.getByRole("button", { name: "Search" });
    expect(button).toBeDisabled();
  });

  it("does not call onSearch if only origin is entered", async () => {
    const onSearch = vi.fn();
    const user = userEvent.setup();
    render(<SearchForm onSearch={onSearch} loading={false} />);

    await user.type(screen.getByLabelText("From (City)"), "Dallas");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(onSearch).not.toHaveBeenCalled();
  });
});
