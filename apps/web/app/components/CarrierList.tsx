"use client";

interface Carrier {
  carrier_name: string;
  trucks_per_day: number;
}

interface SearchResult {
  origin: string;
  destination: string;
  carriers: Carrier[];
  total_carriers: number;
}

interface CarrierListProps {
  result: SearchResult | null;
}

export default function CarrierList({ result }: CarrierListProps) {
  if (!result) {
    return (
      <div className="empty-state">
        <p>Select origin and destination cities to find carriers on this route.</p>
      </div>
    );
  }

  if (result.carriers.length === 0) {
    return (
      <div className="empty-state">
        <p>No carriers found for this route. Try a different city pair.</p>
      </div>
    );
  }

  return (
    <div className="carrier-list">
      <div className="route-info">
        <span className="route-city">{result.origin}</span>
        <span className="route-arrow">&rarr;</span>
        <span className="route-city">{result.destination}</span>
        <span className="route-meta">
          {result.total_carriers} carrier{result.total_carriers !== 1 ? "s" : ""} found
        </span>
      </div>

      <table className="carrier-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Carrier</th>
            <th>Trucks / Day</th>
          </tr>
        </thead>
        <tbody>
          {result.carriers.map((carrier, index) => (
            <tr key={carrier.carrier_name}>
              <td className="carrier-rank">#{index + 1}</td>
              <td className="carrier-name">{carrier.carrier_name}</td>
              <td>
                <span className="trucks-badge">
                  {carrier.trucks_per_day}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
