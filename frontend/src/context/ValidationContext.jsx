import React, { createContext, useContext, useState } from 'react';

const ValidationContext = createContext(null);

export function ValidationProvider({ children }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const value = { result, setResult, loading, setLoading, error, setError };

  return (
    <ValidationContext.Provider value={value}>
      {children}
    </ValidationContext.Provider>
  );
}

export const useValidation = () => useContext(ValidationContext);
