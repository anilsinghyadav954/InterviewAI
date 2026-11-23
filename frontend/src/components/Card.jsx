import React from 'react';

const Card = ({
  children,
  title,
  subtitle,
  icon: Icon,
  headerAction,
  footer,
  className = '',
  bodyClassName = '',
  hoverEffect = false,
  padding = 'normal',
}) => {
  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    normal: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`
        bg-white border border-slate-200/80 rounded-2xl shadow-xs transition-all duration-200
        ${hoverEffect ? 'hover:shadow-md hover:border-slate-300' : ''}
        ${className}
      `}
    >
      {(title || subtitle || Icon || headerAction) && (
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center shrink-0">
                <Icon className="w-5 h-5" />
              </div>
            )}
            <div>
              {title && (
                <h3 className="text-base font-semibold text-slate-900 leading-tight">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className={`${paddings[padding] || paddings.normal} ${bodyClassName}`}>
        {children}
      </div>
      {footer && (
        <div className="px-6 py-4 bg-slate-50/70 border-t border-slate-100 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
