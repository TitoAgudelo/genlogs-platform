import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import CarrierList from "../CarrierList";

describe("CarrierList", () => {
  it("shows empty state when result is null", () => {
    render(<CarrierList result={null} />);
    expect(
      screen.getByText("Select origin and destination cities to find carriers on this route.")
    ).toBeInTheDocument();
  });

  it("shows no-carriers message when carriers array is empty", () => {
    render(
      <CarrierList
        result={{
          origin: "Dallas",
          destination: "Houston",
          carriers: [],
          total_carriers: 0,
        }}
      />
    );
    expect(
      screen.getByText("No carriers found for this route. Try a different city pair.")
    ).toBeInTheDocument();
  });

  it("renders carrier table with ranking when carriers exist", () => {
    render(
      <CarrierList
        result={{
          origin: "Dallas",
          destination: "Houston",
          carriers: [
            { carrier_name: "FedEx", trucks_per_day: 12 },
            { carrier_name: "UPS", trucks_per_day: 8 },
          ],
          total_carriers: 2,
        }}
      />
    );

    expect(screen.getByText("Dallas")).toBeInTheDocument();
    expect(screen.getByText("Houston")).toBeInTheDocument();
    expect(screen.getByText("2 carriers found")).toBeInTheDocument();

    // Check table headers
    expect(screen.getByText("Rank")).toBeInTheDocument();
    expect(screen.getByText("Carrier")).toBeInTheDocument();
    expect(screen.getByText("Trucks / Day")).toBeInTheDocument();

    // Check ranking
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("#2")).toBeInTheDocument();

    // Check carrier data
    expect(screen.getByText("FedEx")).toBeInTheDocument();
    expect(screen.getByText("UPS")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("uses singular 'carrier' when total_carriers is 1", () => {
    render(
      <CarrierList
        result={{
          origin: "A",
          destination: "B",
          carriers: [{ carrier_name: "Solo", trucks_per_day: 1 }],
          total_carriers: 1,
        }}
      />
    );
    expect(screen.getByText("1 carrier found")).toBeInTheDocument();
  });
});
