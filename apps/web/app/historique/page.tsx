import type { Metadata } from "next";
import HistoryPanel from "./HistoryPanel";
export const metadata: Metadata = { title: "Historique — VEYRA" };
export default function Historique() {
  return (
    <div className="container narrow page">
      <h1>Historique</h1>
      <HistoryPanel />
    </div>
  );
}
