import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const colorStyles = {
  indigo: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-100',
    iconColor: 'text-indigo-600',
  },
  emerald: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-100',
    iconColor: 'text-emerald-600',
  },
  blue: {
    bg: 'bg-blue-50',
    border: 'border-blue-100',
    iconColor: 'text-blue-600',
  },
  amber: {
    bg: 'bg-amber-50',
    border: 'border-amber-100',
    iconColor: 'text-amber-600',
  },
  purple: {
    bg: 'bg-purple-50',
    border: 'border-purple-100',
    iconColor: 'text-purple-600',
  },
};

const StatCard = ({
  label,
  value,
  change,
  trend = 'up',
  icon: Icon,
  color = 'indigo',
  subtitle,
}) => {
  const currentTheme = colorStyles[color] || colorStyles.indigo;

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs hover:shadow-md transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        {Icon && (
          <div
            className={`w-11 h-11 rounded-xl ${currentTheme.bg} ${currentTheme.border} border ${currentTheme.iconColor} flex items-center justify-center shrink-0`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-4 flex items-baseline justify-between gap-2">
        <h4 className="text-3xl font-bold tracking-tight text-slate-900">
          {value}
        </h4>
        {change && (
          <span
            className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
              trend === 'up'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-rose-50 text-rose-700'
            }`}
          >
            {trend === 'up' ? (
              <ArrowUpRight className="w-3 h-3 mr-0.5" />
            ) : (
              <ArrowDownRight className="w-3 h-3 mr-0.5" />
            )}
            {change}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-slate-400 font-normal">{subtitle}</p>
      )}
    </div>
  );
};

export default StatCard;
