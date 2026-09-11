import { HTMLAttributes } from "react";
import clsx from "clsx";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-3xl border border-black/5 bg-white p-6 shadow-[0_14px_30px_-18px_rgba(60,40,25,0.35)]",
        className
      )}
      {...props}
    />
  );
}
