import { useState, useCallback, useMemo } from 'react';

export function useHiddenSlices(initial = []){
  const [hiddenSlices, setHiddenSlices] = useState(()=> new Set(initial));
  const toggleSlice = useCallback((name)=>{
    setHiddenSlices(prev => { const next=new Set(prev); if (next.has(name)) next.delete(name); else next.add(name); return next; });
  },[]);
  const resetSlices = useCallback(()=> setHiddenSlices(new Set()), []);
  const isHidden = useCallback((name)=> hiddenSlices.has(name), [hiddenSlices]);
  return { hiddenSlices, toggleSlice, resetSlices, isHidden };
}
