"use client";

import { useEffect, useCallback, useRef } from "react";

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: () => void;
  description?: string;
  preventDefault?: boolean;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    const target = e.target as HTMLElement;
    if (
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.isContentEditable
    ) {
      return;
    }

    for (const shortcut of shortcutsRef.current) {
      const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();
      const ctrlMatch = !!shortcut.ctrl === (e.ctrlKey || e.metaKey);
      const shiftMatch = !!shortcut.shift === e.shiftKey;
      const altMatch = !!shortcut.alt === e.altKey;

      if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
        if (shortcut.preventDefault !== false) {
          e.preventDefault();
        }
        shortcut.action();
        return;
      }
    }
  }, []);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

// Common shortcut keys with display labels
export const shortcutLabels: Record<string, string> = {
  ctrl: "Ctrl",
  meta: "Cmd",
  shift: "Shift",
  alt: "Alt",
  enter: "Enter",
  escape: "Esc",
  space: "Space",
  backspace: "Backspace",
  delete: "Del",
  arrowup: "Up",
  arrowdown: "Down",
  arrowleft: "Left",
  arrowright: "Right",
};

export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];
  
  if (shortcut.ctrl) {
    parts.push(navigator.platform.includes("Mac") ? "Cmd" : "Ctrl");
  }
  if (shortcut.shift) parts.push("Shift");
  if (shortcut.alt) parts.push("Alt");
  
  const keyLabel = shortcutLabels[shortcut.key.toLowerCase()] || shortcut.key.toUpperCase();
  parts.push(keyLabel);
  
  return parts.join(" + ");
}
