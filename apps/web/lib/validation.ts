// Vérifications réelles effectuées côté navigateur avant l'envoi.
// Le backend (Phase 3) refera ces vérifications : ne jamais faire confiance au client seul.
import type { ContentType } from "./types";

export const LIMITS = {
  text: { minChars: 300, maxChars: 20000 },
  image: { maxBytes: 4 * 1024 * 1024, mime: ["image/jpeg", "image/png", "image/webp", "image/heic"] },
  video: { maxBytes: 100 * 1024 * 1024, mime: ["video/mp4", "video/quicktime", "video/webm"] },
} as const;

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} o`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} Ko`;
  return `${(n / 1024 / 1024).toFixed(1)} Mo`;
}

export function validateText(text: string): string | null {
  const len = text.trim().length;
  if (len < LIMITS.text.minChars)
    return `Le texte est trop court (${len} caractères). Minimum : ${LIMITS.text.minChars} caractères pour une analyse utile.`;
  if (len > LIMITS.text.maxChars)
    return `Le texte est trop long (${len} caractères). Maximum : ${LIMITS.text.maxChars}.`;
  return null;
}

export function validateFile(type: Exclude<ContentType, "text">, file: File): string | null {
  const rule = LIMITS[type];
  if (!(rule.mime as readonly string[]).includes(file.type))
    return `Format non autorisé (${file.type || "inconnu"}). Formats acceptés : ${rule.mime.map((m) => m.split("/")[1].toUpperCase()).join(", ")}.`;
  if (file.size > rule.maxBytes)
    return `Fichier trop lourd (${formatBytes(file.size)}). Maximum : ${formatBytes(rule.maxBytes)}.`;
  return null;
}
