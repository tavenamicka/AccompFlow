"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import clsx from "clsx";
import { IconDots } from "@/components/icons";

interface RowAction {
  label: string;
  onClick: () => void;
  variant?: "default" | "danger";
}

interface RowActionsMenuProps {
  actions: RowAction[];
  disabled?: boolean;
}

const MENU_WIDTH = 176; // w-44

export function RowActionsMenu({ actions, disabled }: RowActionsMenuProps) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (buttonRef.current?.contains(target) || menuRef.current?.contains(target)) return;
      setOpen(false);
    };
    const close = () => setOpen(false);
    document.addEventListener("mousedown", onClickOutside);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [open]);

  const toggle = () => {
    if (!open && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setPosition({ top: rect.bottom + 4, left: rect.right - MENU_WIDTH });
    }
    setOpen((v) => !v);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        aria-label="Actions"
        aria-expanded={open}
        disabled={disabled}
        onClick={toggle}
        className="inline-flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-sand/70 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <IconDots className="h-5 w-5" />
      </button>
      {open &&
        position &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            ref={menuRef}
            style={{ position: "fixed", top: position.top, left: position.left, width: MENU_WIDTH }}
            className="z-50 overflow-hidden rounded-2xl border border-black/5 bg-white py-1 shadow-lg"
          >
            {actions.map((action) => (
              <button
                key={action.label}
                type="button"
                onClick={() => {
                  setOpen(false);
                  action.onClick();
                }}
                className={clsx(
                  "block w-full px-4 py-2 text-left text-sm font-semibold transition-colors hover:bg-cream",
                  action.variant === "danger" ? "text-red-600" : "text-slate-700"
                )}
              >
                {action.label}
              </button>
            ))}
          </div>,
          document.body
        )}
    </>
  );
}
