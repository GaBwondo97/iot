import React from 'react';
import { City } from '../../types';

interface HeaderProps {
  cities: City[];
  currentCity: City | null;
  onCityChange: (cityCode: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ cities, currentCity, onCityChange }) => {
  return (
    <header className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-tight">CityPulse AI</span>
      </div>
      <nav className="flex items-center gap-4">
        <label htmlFor="city-select" className="text-sm text-slate-400">City:</label>
        <select
          id="city-select"
          value={currentCity?.city_code || ''}
          onChange={(e) => onCityChange(e.target.value)}
          className="bg-slate-800 text-white text-sm rounded-md px-3 py-1.5 border border-slate-700 focus:outline-none"
          disabled={cities.length === 0}
        >
          {cities.map((city) => (
            <option key={city.id} value={city.city_code}>{city.name} ({city.city_code})</option>
          ))}
        </select>
      </nav>
    </header>
  );
};