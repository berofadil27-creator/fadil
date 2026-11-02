// Historique lié au compte (Phase 7.2), stocké dans Supabase (table public.analyses).
// Seul le rapport est enregistré : jamais le texte, la photo ou la vidéo analysés.
// Les règles RLS de Supabase limitent chaque utilisateur à ses propres analyses.
import type { AnalysisResult } from "./types";
import { supabase } from "./supabase";

export interface HistoryRow {
  id: string;
  content_type: AnalysisResult["content_type"];
  conclusion: AnalysisResult["conclusion"];
  result: AnalysisResult;
  created_at: string;
}

export async function currentUserId(): Promise<string | null> {
  const sb = supabase();
  if (!sb) return null;
  const { data } = await sb.auth.getSession();
  return data.session?.user.id ?? null;
}

/** Enregistre le rapport si l'utilisateur est connecté. Renvoie true si c'est fait. */
export async function saveToHistory(r: AnalysisResult): Promise<boolean> {
  const sb = supabase();
  if (!sb || r.status !== "completed" || !(await currentUserId())) return false;
  const { error } = await sb.from("analyses").insert({
    id: r.analysis_id, content_type: r.content_type, conclusion: r.conclusion, result: r,
  });
  return !error;
}

export async function listHistory(): Promise<HistoryRow[]> {
  const sb = supabase();
  if (!sb) return [];
  const { data, error } = await sb.from("analyses")
    .select("id, content_type, conclusion, result, created_at")
    .order("created_at", { ascending: false }).limit(100);
  if (error) throw new Error("Impossible de charger l'historique. Réessayez.");
  return (data ?? []) as HistoryRow[];
}

export async function deleteFromHistory(id: string): Promise<void> {
  const sb = supabase();
  if (!sb) return;
  const { error } = await sb.from("analyses").delete().eq("id", id);
  if (error) throw new Error("La suppression a échoué. Réessayez.");
}
