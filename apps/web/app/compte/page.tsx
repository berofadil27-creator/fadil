import type { Metadata } from "next";
import AccountPanel from "./AccountPanel";
export const metadata: Metadata = { title: "Compte — VEYRA" };
export default function Compte() {
  return (
    <div className="container narrow page">
      <h1>Compte</h1>
      <AccountPanel />
    </div>
  );
}
