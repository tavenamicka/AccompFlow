import { TextareaHTMLAttributes, forwardRef, useCallback, useLayoutEffect, useRef } from "react";
import clsx from "clsx";

// Zone multi-ligne qui s'agrandit avec son contenu (pas de barre de défilement interne).
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, value, ...props }, ref) => {
    const inner = useRef<HTMLTextAreaElement | null>(null);

    const setRefs = useCallback(
      (node: HTMLTextAreaElement | null) => {
        inner.current = node;
        if (typeof ref === "function") ref(node);
        else if (ref) ref.current = node;
      },
      [ref]
    );

    useLayoutEffect(() => {
      const el = inner.current;
      if (!el) return;
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }, [value]);

    return (
      <textarea
        ref={setRefs}
        rows={3}
        value={value}
        className={clsx(
          "block min-h-[5.5rem] w-full resize-none overflow-hidden rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm leading-relaxed focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";
