import React from 'react';

const Input = ({
  label,
  id,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  helperText,
  icon: Icon,
  endIcon: EndIcon,
  onEndIconClick,
  disabled = false,
  required = false,
  className = '',
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between items-center mb-1.5">
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-slate-700 tracking-wide"
          >
            {label}
            {required && <span className="text-rose-500 ml-1">*</span>}
          </label>
        </div>
      )}
      <div className="relative rounded-xl shadow-xs">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          id={inputId}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`
            block w-full rounded-xl text-sm transition-colors duration-150
            py-2.5 px-3.5
            ${Icon ? 'pl-10' : ''}
            ${EndIcon ? 'pr-10' : ''}
            ${
              error
                ? 'border-rose-300 text-rose-900 placeholder-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-rose-500 bg-rose-50/20'
                : 'border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white'
            }
            ${disabled ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}
          `}
          {...props}
        />
        {EndIcon && (
          <button
            type="button"
            onClick={onEndIconClick}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
          >
            <EndIcon className="w-4 h-4" />
          </button>
        )}
      </div>
      {error ? (
        <p className="mt-1.5 text-xs text-rose-600 font-medium">{error}</p>
      ) : helperText ? (
        <p className="mt-1.5 text-xs text-slate-500">{helperText}</p>
      ) : null}
    </div>
  );
};

export default Input;
