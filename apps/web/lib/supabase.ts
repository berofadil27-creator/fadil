// Client Supabase (Phase 7). Seules la clé publique et l'URL du projet sont utilisées ici :
// la clé secrète ne doit JAMAIS se trouver dans le site.
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

let client: SupabaseClient | null = null;

export function supabase(): SupabaseClient | null {
  if (!url || !key) return null;
  if (!client) client = createClient(url, key, { auth: { persistSession: true, autoRefreshToken: true } });
  return client;
}

// Messages d'erreur Supabase traduits en français clair.
export function authErrorFr(message: string): string {
  const m = message.toLowerCase();
  if (m.includes("invalid login credentials")) return "Email ou mot de passe incorrect.";
  if (m.includes("email not confirmed")) return "Confirmez d'abord votre adresse email (lien reçu par email).";
  if (m.includes("already registered")) return "Un compte existe déjà avec cet email. Connectez-vous.";
  if (m.includes("password should be")) return "Mot de passe trop faible : 8 caractères minimum.";
  if (m.includes("rate limit") || m.includes("too many")) return "Trop de tentatives. Réessayez dans quelques minutes.";
  if (m.includes("invalid") && m.includes("email")) return "Adresse email invalide.";
  return "Une erreur est survenue. Réessayez.";
}
