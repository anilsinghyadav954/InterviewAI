import React from 'react';

const Loading = ({
  size = 'md',
  text = 'Loading...',
  fullPage = false,
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  const content = (
    <div className={`flex flex-col items-center justify-center p-6 gap-3 ${className}`}>
      <div
        className={`${sizeClasses[size] || sizeClasses.md} rounded-full border-slate-200 border-t-indigo-600 animate-spin`}
      />
      {text && <p className="text-xs font-medium text-slate-500">{text}</p>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 bg-white/80 backdrop-blur-xs flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
};

export default Loading;
