"use client";

import React, { useState, useCallback, useRef } from "react";
import { motion, Reorder, useDragControls } from "framer-motion";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface DraggableItemProps<T> {
  item: T;
  renderItem: (item: T, isDragging: boolean) => React.ReactNode;
  showHandle?: boolean;
  className?: string;
}

function DraggableItem<T extends { id: string | number }>({
  item,
  renderItem,
  showHandle = true,
  className,
}: DraggableItemProps<T>) {
  const controls = useDragControls();
  const [isDragging, setIsDragging] = useState(false);

  return (
    <Reorder.Item
      value={item}
      id={String(item.id)}
      dragListener={!showHandle}
      dragControls={controls}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={() => setIsDragging(false)}
      className={cn(
        "relative flex items-center gap-2",
        isDragging && "z-50",
        className
      )}
      whileDrag={{
        scale: 1.02,
        boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
      }}
    >
      {showHandle && (
        <button
          className="p-1 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground transition-colors touch-none"
          onPointerDown={(e) => controls.start(e)}
        >
          <GripVertical className="w-4 h-4" />
        </button>
      )}
      <div className="flex-1">{renderItem(item, isDragging)}</div>
    </Reorder.Item>
  );
}

interface DraggableListProps<T extends { id: string | number }> {
  items: T[];
  onReorder: (items: T[]) => void;
  renderItem: (item: T, isDragging: boolean) => React.ReactNode;
  showHandle?: boolean;
  className?: string;
  itemClassName?: string;
  axis?: "x" | "y";
}

export function DraggableList<T extends { id: string | number }>({
  items,
  onReorder,
  renderItem,
  showHandle = true,
  className,
  itemClassName,
  axis = "y",
}: DraggableListProps<T>) {
  return (
    <Reorder.Group
      axis={axis}
      values={items}
      onReorder={onReorder}
      className={cn("space-y-1", className)}
    >
      {items.map((item) => (
        <DraggableItem
          key={item.id}
          item={item}
          renderItem={renderItem}
          showHandle={showHandle}
          className={itemClassName}
        />
      ))}
    </Reorder.Group>
  );
}

// Simple sortable grid for cards
interface SortableGridProps<T extends { id: string | number }> {
  items: T[];
  onReorder: (items: T[]) => void;
  renderItem: (item: T, index: number) => React.ReactNode;
  columns?: number;
  gap?: number;
  className?: string;
}

export function SortableGrid<T extends { id: string | number }>({
  items,
  onReorder,
  renderItem,
  columns = 3,
  gap = 16,
  className,
}: SortableGridProps<T>) {
  const [draggedItem, setDraggedItem] = useState<T | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const handleDragStart = useCallback((item: T) => {
    setDraggedItem(item);
  }, []);

  const handleDragOver = useCallback((index: number) => {
    setDragOverIndex(index);
  }, []);

  const handleDragEnd = useCallback(() => {
    if (draggedItem && dragOverIndex !== null) {
      const currentIndex = items.findIndex((i) => i.id === draggedItem.id);
      if (currentIndex !== dragOverIndex) {
        const newItems = [...items];
        newItems.splice(currentIndex, 1);
        newItems.splice(dragOverIndex, 0, draggedItem);
        onReorder(newItems);
      }
    }
    setDraggedItem(null);
    setDragOverIndex(null);
  }, [draggedItem, dragOverIndex, items, onReorder]);

  return (
    <div
      className={cn("grid", className)}
      style={{
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap,
      }}
    >
      {items.map((item, index) => (
        <motion.div
          key={item.id}
          draggable
          onDragStart={() => handleDragStart(item)}
          onDragOver={(e) => {
            e.preventDefault();
            handleDragOver(index);
          }}
          onDragEnd={handleDragEnd}
          className={cn(
            "cursor-grab active:cursor-grabbing",
            dragOverIndex === index && "ring-2 ring-primary ring-offset-2"
          )}
          whileDrag={{ scale: 1.05, zIndex: 50 }}
        >
          {renderItem(item, index)}
        </motion.div>
      ))}
    </div>
  );
}
