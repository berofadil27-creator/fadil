// Lecture de la provenance C2PA (Content Credentials) d'une vidéo, DANS le navigateur (étape 8.5).
// La vidéo n'est jamais envoyée : seul un court résumé (état, émetteur, outil, types de source
// déclarés) part au serveur avec les images extraites. Ce résumé est produit par l'appareil de
// l'utilisateur : le serveur ne peut pas le vérifier lui-même, et le rapport le dit.
// Le module (~9 Mo) n'est chargé que lorsqu'une vidéo est analysée.

export type ClientProvenanceStatus = "absent" | "invalid" | "valid" | "trusted" | "error";

export interface ClientProvenance {
  status: ClientProvenanceStatus;
  issuer: string | null;
  generator: string | null;
  source_types: string[];
}

const IPTC = "http://cv.iptc.org/newscodes/digitalsourcetype/";
const TIMEOUT_MS = 20000;

function mimeOf(file: File): string {
  if (file.type) return file.type;
  const ext = file.name.split(".").pop()?.toLowerCase();
  return ext === "mov" ? "video/quicktime" : ext === "webm" ? "video/webm" : "video/mp4";
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function sourceTypes(store: any): string[] {
  const found = new Set<string>();
  for (const m of Object.values(store?.manifests ?? {}) as any[]) {
    for (const a of m?.assertions ?? []) {
      if (!String(a?.label ?? "").startsWith("c2pa.actions")) continue;
      for (const act of a?.data?.actions ?? []) {
        const d = String(act?.digitalSourceType ?? "");
        if (d.startsWith(IPTC)) found.add(d.slice(IPTC.length));
      }
    }
  }
  return [...found].slice(0, 10);
}

async function read(file: File): Promise<ClientProvenance> {
  const { createC2pa, Reader, Context } = await import("@contentauth/c2pa-web");
  const c2pa = await createC2pa({ wasmSrc: "/c2pa/c2pa_bg.wasm" });
  try {
    // Aucune adresse distante n'est ouverte à partir d'un fichier inconnu.
    const ctx = new Context({ verify: { remoteManifestFetch: false } });
    const reader = await Reader.fromBlob(c2pa, mimeOf(file), file, ctx);
    if (!reader) return { status: "absent", issuer: null, generator: null, source_types: [] };
    try {
      const store: any = await reader.manifestStore();
      const active: any = store?.manifests?.[store?.active_manifest ?? ""] ?? {};
      const state = String(store?.validation_state ?? "").toLowerCase();
      const gen = active?.claim_generator ?? active?.claim_generator_info?.[0]?.name ?? null;
      return {
        status: state === "trusted" ? "trusted" : state === "valid" ? "valid" : "invalid",
        issuer: active?.signature_info?.issuer ? String(active.signature_info.issuer).slice(0, 200) : null,
        generator: gen ? String(gen).slice(0, 200) : null,
        source_types: sourceTypes(store),
      };
    } finally {
      await reader.free().catch(() => {});
    }
  } finally {
    c2pa.dispose();
  }
}

export async function readVideoProvenance(file: File): Promise<ClientProvenance> {
  const fail: ClientProvenance = { status: "error", issuer: null, generator: null, source_types: [] };
  try {
    return await Promise.race([
      read(file),
      new Promise<ClientProvenance>((resolve) => setTimeout(() => resolve(fail), TIMEOUT_MS)),
    ]);
  } catch (e) {
    const msg = String((e as Error)?.message ?? e);
    if (/ManifestNotFound|JumbfNotFound|no manifest/i.test(msg)) {
      return { status: "absent", issuer: null, generator: null, source_types: [] };
    }
    return fail;
  }
}
