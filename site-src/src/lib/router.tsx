import { useEffect, useState, type AnchorHTMLAttributes, type ReactNode } from "react";

export function navigate(to: string) {
  window.history.pushState({}, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function useLocation() {
  const [loc, setLoc] = useState({ path: window.location.pathname, hash: window.location.hash });
  useEffect(() => {
    const on = () => setLoc({ path: window.location.pathname, hash: window.location.hash });
    window.addEventListener("popstate", on);
    return () => window.removeEventListener("popstate", on);
  }, []);
  return loc;
}

export function Link({
  to,
  hash = "",
  children,
  ...rest
}: { to: string; hash?: string; children: ReactNode } & AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a
      href={to + hash}
      {...rest}
      onClick={(e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        navigate(to + hash);
      }}
    >
      {children}
    </a>
  );
}
