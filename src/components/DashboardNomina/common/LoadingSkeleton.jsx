import React from 'react';

const LoadingSkeleton = ({ variant='movimientos' }) => {
  if (variant === 'libro') {
    return (
      <div className="p-8 text-gray-300">Cargando libro...</div>
    );
  }
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gray-800 animate-pulse" />
            <div className="space-y-2">
              <div className="h-4 w-56 bg-gray-800 rounded animate-pulse" />
              <div className="h-3 w-40 bg-gray-800 rounded animate-pulse" />
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-900/60 rounded-xl p-6 border border-gray-800">
              <div className="h-5 w-24 bg-gray-800 rounded animate-pulse mb-4" />
              <div className="h-7 w-32 bg-gray-800 rounded animate-pulse" />
            </div>
          ))}
        </div>
        <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="grid grid-cols-6 gap-4 p-4 border-b border-gray-800">
              {[...Array(6)].map((__, j) => (
                <div key={j} className="h-4 bg-gray-800 rounded animate-pulse" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingSkeleton;
