import React from 'react';
import { ChevronDown } from 'lucide-react';

const Select = ({
  label,
  id,
  options = [],
  value,
  onChange,
  error,
  helperText,
  placeholder = 'Select an option',
  disabled = false,
  required = false,
  className = '',
  ...props
}) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label
          htmlFor={selectId}
          className="block text-xs font-semibold text-slate-700 tracking-wide mb-1.5"
        >
          {label}
          {required && <span className="text-rose-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative rounded-xl shadow-xs">
        <select
          id={selectId}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          className={`
            appearance-none block w-full rounded-xl text-sm transition-colors duration-150
            py-2.5 pl-3.5 pr-10
            ${
              error
                ? 'border-rose-300 text-rose-900 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-rose-500 bg-rose-50/20'
                : 'border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white'
            }
            ${disabled ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : 'cursor-pointer'}
          `}
          {...props}
        >
          {placeholder && (
            <option value="" disabled className="text-slate-400">
              {placeholder}
            </option>
          )}
          {options.map((opt) => {
            const optVal = typeof opt === 'object' ? opt.value : opt;
            const optLabel = typeof opt === 'object' ? opt.label : opt;
            return (
              <option key={optVal} value={optVal}>
                {optLabel}
              </option>
            );
          })}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400">
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>
      {error ? (
        <p className="mt-1.5 text-xs text-rose-600 font-medium">{error}</p>
      ) : helperText ? (
        <p className="mt-1.5 text-xs text-slate-500">{helperText}</p>
      ) : null}
    </div>
  );
};

export default Select;
