import React from 'react';

interface HeaderProps {
  selectedCity: string;
  onCityChange: (city: string) => void;
  cities: string[];
}

export const Header: React.FC<HeaderProps> = ({ selectedCity, onCityChange, cities }) => {
  return (
    <header className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-tight">CityRisk Monitor</span>
      </div>
      <nav className="flex items-center gap-4">
        <label htmlFor="city-select" className="text-sm text-slate-400">City:</label>
        <select
          id="city-select"
          value={selectedCity}
          onChange={(e) => onCityChange(e.target.value)}
          className="bg-slate-800 text-white text-sm rounded-md px-3 py-1.5 border border-slate-700 focus:outline-none"
        >
          {cities.map((city) => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </nav>
    </header>
  );
};
