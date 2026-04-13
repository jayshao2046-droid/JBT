"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  separator?: boolean;
  onClick?: () => void;
  children?: ContextMenuItem[];
}

interface ContextMenuWrapperProps {
  children: React.ReactNode;
  items: ContextMenuItem[];
  className?: string;
  disabled?: boolean;
}

export function ContextMenuWrapper({
  children,
  items,
  className,
  disabled = false,
}: ContextMenuWrapperProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [submenuOpen, setSubmenuOpen] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      if (disabled) return;
      e.preventDefault();
      e.stopPropagation();

      const x = e.clientX;
      const y = e.clientY;

      // Adjust position if menu would overflow viewport
      const menuWidth = 200;
      const menuHeight = items.length * 36 + 16;
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      setPosition({
        x: x + menuWidth > viewportWidth ? x - menuWidth : x,
        y: y + menuHeight > viewportHeight ? y - menuHeight : y,
      });

      setIsOpen(true);
    },
    [disabled, items.length]
  );

  const handleClick = useCallback((item: ContextMenuItem) => {
    if (item.disabled) return;
    item.onClick?.();
    setIsOpen(false);
    setSubmenuOpen(null);
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSubmenuOpen(null);
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
        setSubmenuOpen(null);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  return (
    <div ref={containerRef} className={className} onContextMenu={handleContextMenu}>
      {children}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={menuRef}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            className="fixed z-[100] min-w-[180px] bg-popover border border-border rounded-lg shadow-lg py-1 overflow-hidden"
            style={{ left: position.x, top: position.y }}
          >
            {items.map((item) =>
              item.separator ? (
                <div key={item.id} className="my-1 h-px bg-border" />
              ) : (
                <div key={item.id} className="relative">
                  <button
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 text-sm text-left transition-colors",
                      item.disabled
                        ? "text-muted-foreground cursor-not-allowed"
                        : item.danger
                        ? "text-destructive hover:bg-destructive/10"
                        : "text-foreground hover:bg-muted",
                      item.children && "pr-8"
                    )}
                    onClick={() => handleClick(item)}
                    onMouseEnter={() => item.children && setSubmenuOpen(item.id)}
                    onMouseLeave={() => !item.children && setSubmenuOpen(null)}
                    disabled={item.disabled}
                  >
                    {item.icon && <span className="w-4 h-4 flex items-center justify-center">{item.icon}</span>}
                    <span className="flex-1">{item.label}</span>
                    {item.shortcut && (
                      <span className="text-xs text-muted-foreground ml-auto">{item.shortcut}</span>
                    )}
                    {item.children && (
                      <svg className="w-3 h-3 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </button>

                  {/* Submenu */}
                  <AnimatePresence>
                    {item.children && submenuOpen === item.id && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        className="absolute left-full top-0 ml-1 min-w-[160px] bg-popover border border-border rounded-lg shadow-lg py-1"
                        onMouseEnter={() => setSubmenuOpen(item.id)}
                        onMouseLeave={() => setSubmenuOpen(null)}
                      >
                        {item.children.map((child) => (
                          <button
                            key={child.id}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2 text-sm text-left transition-colors",
                              child.disabled
                                ? "text-muted-foreground cursor-not-allowed"
                                : "text-foreground hover:bg-muted"
                            )}
                            onClick={() => handleClick(child)}
                            disabled={child.disabled}
                          >
                            {child.icon && <span className="w-4 h-4">{child.icon}</span>}
                            <span className="flex-1">{child.label}</span>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
