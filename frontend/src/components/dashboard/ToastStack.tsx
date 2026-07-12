import React, { useState, useCallback, useEffect, useRef } from 'react';

export interface Toast {
  id: string;
  text: string;
  category: 'crime' | 'economy' | 'social' | 'policy' | 'system';
}

const ICONS: Record<string, string> = {
  crime: '\u{1F4A2}', economy: '\u{1F4B0}', social: '\u{1F91D}',
  policy: '\u{2696}\uFE0F', system: '\u{2699}\uFE0F',
};

const ToastStack: React.FC = () => {
  const [toasts, setToasts] = useState<(Toast & { leaving?: boolean })[]>([]);
  const counterRef = useRef(0);

  const addToast = useCallback((text: string, category: Toast['category'] = 'system') => {
    const id = `t${++counterRef.current}`;
    setToasts(prev => [...prev, { id, text, category }]);
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, leaving: true } : t));
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 300);
    }, 4000);
  }, []);

  // Expose addToast globally for other components
  useEffect(() => {
    (window as any).__addToast = addToast;
    return () => { delete (window as any).__addToast; };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.category}${t.leaving ? ' leaving' : ''}`}>
          <span className="toast-ic">{ICONS[t.category]}</span>
          <span className="toast-txt">{t.text}</span>
        </div>
      ))}
    </div>
  );
};

export default ToastStack;
