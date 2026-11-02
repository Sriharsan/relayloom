import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { useLocation } from "@/lib/router";
import { SiteFooter, SiteHeader } from "@/components/layout";
import { Home } from "@/pages/home";
import { Proof } from "@/pages/proof";
import { Demo } from "@/pages/demo";

const TITLES: Record<string, string> = {
  "/": "Relayloom. Accounts payable that checks the goods.",
  "/proof": "Proof. Relayloom, measured on synthetic data.",
  "/demo": "Demo. Replay of a Relayloom run.",
};

function App() {
  const { path, hash } = useLocation();
  const page = path.replace(/\/+$/, "") || "/";
  useEffect(() => {
    document.title = TITLES[page] ?? TITLES["/"];
    if (hash) {
      requestAnimationFrame(() => document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "smooth" }));
    } else {
      window.scrollTo(0, 0);
    }
  }, [page, hash]);
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">{page === "/proof" ? <Proof /> : page === "/demo" ? <Demo /> : <Home />}</main>
      <SiteFooter />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
