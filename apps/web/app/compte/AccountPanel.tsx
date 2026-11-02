"use client";
import { useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";
import { authErrorFr, supabase } from "@/lib/supabase";

type Mode = "login" | "signup";

export default function AccountPanel() {
  const sb = supabase();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  useEffect(() => {
    if (!sb) { setReady(true); return; }
    sb.auth.getUser().then(({ data }) => { setUser(data.user); setReady(true); });
    const { data } = sb.auth.onAuthStateChange((_e, session) => setUser(session?.user ?? null));
    return () => data.subscription.unsubscribe();
  }, [sb]);

  if (!sb)
    return (
      <div className="card empty">
        <h2>Comptes indisponibles</h2>
        <p className="muted">Le service de comptes n&apos;est pas configuré sur ce serveur.</p>
      </div>
    );
  if (!ready) return <div className="card empty"><p className="muted">Chargement…</p></div>;

  if (user)
    return (
      <div className="card empty">
        <h2>Connecté</h2>
        <p>{user.email}</p>
        <p className="muted small">Compte créé le {new Date(user.created_at).toLocaleDateString("fr-FR")}</p>
        <p className="muted small">L&apos;historique lié au compte et la suppression du compte arrivent dans les prochaines étapes.</p>
        <button className="btn btn-primary full" onClick={() => sb.auth.signOut()}>Se déconnecter</button>
      </div>
    );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null); setInfo(null);
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Adresse email invalide.");
    if (password.length < 8) return setError("Mot de passe trop court : 8 caractères minimum.");
    if (mode === "signup" && password !== confirm) return setError("Les deux mots de passe ne correspondent pas.");
    setBusy(true);
    try {
      if (mode === "login") {
        const { error } = await sb!.auth.signInWithPassword({ email, password });
        if (error) setError(authErrorFr(error.message));
      } else {
        const { data, error } = await sb!.auth.signUp({
          email, password, options: { emailRedirectTo: `${window.location.origin}/compte` },
        });
        if (error) setError(authErrorFr(error.message));
        else if (data.user && data.user.identities?.length === 0)
          setError("Un compte existe déjà avec cet email. Connectez-vous.");
        else if (!data.session)
          setInfo("Compte créé. Ouvrez le lien reçu par email pour confirmer votre adresse, puis connectez-vous.");
      }
    } catch {
      setError("Le service de comptes est injoignable. Vérifiez votre connexion.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card empty" onSubmit={submit}>
      <div className="tabs tabs-2" role="tablist">
        {(["login", "signup"] as Mode[]).map((m) => (
          <button key={m} type="button" role="tab" aria-selected={mode === m}
            className={mode === m ? "tab active" : "tab"} onClick={() => { setMode(m); setError(null); setInfo(null); }}>
            {m === "login" ? "Connexion" : "Inscription"}
          </button>
        ))}
      </div>
      <label className="label" htmlFor="email">Email</label>
      <input id="email" className="input" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <label className="label" htmlFor="pw">Mot de passe</label>
      <input id="pw" className="input" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"}
        value={password} onChange={(e) => setPassword(e.target.value)} />
      {mode === "signup" && (
        <>
          <label className="label" htmlFor="pw2">Confirmer le mot de passe</label>
          <input id="pw2" className="input" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      {info && <p className="info" role="status">{info}</p>}
      <button className="btn btn-primary full" disabled={busy}>
        {busy ? "Patientez…" : mode === "login" ? "Se connecter" : "Créer mon compte"}
      </button>
      <p className="muted small center">Le compte est facultatif : l&apos;analyse reste possible sans compte.</p>
    </form>
  );
}
