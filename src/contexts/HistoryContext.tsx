/**
 * HistoryContext - مزود سياق التاريخ
 * يخزن تفاعلات المستخدم السابقة عبر جميع الصفحات
 * كل عنصر يحتوي على أول كلمتين من الإدخال واسم الصفحة
 */
import React, { createContext, useContext, useState, useCallback } from "react";

export interface HistoryItem {
  id: string;
  pageId: string;
  pageName: string;
  preview: string; // أول كلمتين
  timestamp: Date;
}

interface HistoryContextType {
  history: HistoryItem[];
  addHistoryItem: (pageId: string, pageName: string, fullText: string) => void;
  clearHistory: () => void;
}

const HistoryContext = createContext<HistoryContextType | undefined>(undefined);

export const useHistory = () => {
  const ctx = useContext(HistoryContext);
  if (!ctx) throw new Error("useHistory must be used within HistoryProvider");
  return ctx;
};

export const HistoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const addHistoryItem = useCallback((pageId: string, pageName: string, fullText: string) => {
    const words = fullText.trim().split(/\s+/);
    const preview = words.slice(0, 2).join(" ");
    setHistory(prev => [
      {
        id: crypto.randomUUID(),
        pageId,
        pageName,
        preview: preview || "...",
        timestamp: new Date(),
      },
      ...prev,
    ]);
  }, []);

  const clearHistory = useCallback(() => setHistory([]), []);

  return (
    <HistoryContext.Provider value={{ history, addHistoryItem, clearHistory }}>
      {children}
    </HistoryContext.Provider>
  );
};
