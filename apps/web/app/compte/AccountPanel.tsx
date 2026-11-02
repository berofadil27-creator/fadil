"use client";
import { useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";
import { authErrorFr, supabase } from "@/lib/supabase";

type Mode = "login" | "signup" | "forgot";

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
  const [recovery, setRecovery] = useState(false);
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [delText, setDelText] = useState("");

  useEffect(() => {
    if (!sb) { setReady(true); return; }
    sb.auth.getUser().then(({ data }) => { setUser(data.user); setReady(true); });
    const { data } = sb.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      if (event === "PASSWORD_RECOVERY") setRecovery(true);
    });
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

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null); setInfo(null);
    if (newPw.length < 8) return setError("Mot de passe trop court : 8 caractères minimum.");
    if (newPw !== newPw2) return setError("Les deux mots de passe ne correspondent pas.");
    setBusy(true);
    const { error } = await sb!.auth.updateUser({ password: newPw });
    setBusy(false);
    if (error) return setError(authErrorFr(error.message));
    setNewPw(""); setNewPw2(""); setRecovery(false);
    setInfo("Mot de passe modifié.");
  }

  async function deleteAccount() {
    setError(null); setInfo(null);
    if (delText.trim().toUpperCase() !== "SUPPRIMER") return setError("Tapez SUPPRIMER pour confirmer.");
    setBusy(true);
    const { error } = await sb!.rpc("delete_my_account");
    setBusy(false);
    if (error) return setError("La suppression a échoué. Réessayez.");
    await sb!.auth.signOut({ scope: "local" });
    setDelText("");
    setInfo("Votre compte et tout votre historique ont été supprimés.");
  }

  if (user)
    return (
      <>
        <div className="card empty">
          <h2>Connecté</h2>
          <p>{user.email}</p>
          <p className="muted small">Compte créé le {new Date(user.created_at).toLocaleDateString("fr-FR")}</p>
          <button className="btn btn-primary full" onClick={() => sb.auth.signOut()}>Se déconnecter</button>
        </div>

        <form className="card empty" onSubmit={changePassword}>
          <h2>{recovery ? "Choisissez un nouveau mot de passe" : "Changer de mot de passe"}</h2>
          <label className="label" htmlFor="np">Nouveau mot de passe</label>
          <input id="np" className="input" type="password" autoComplete="new-password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
          <label className="label" htmlFor="np2">Confirmer</label>
          <input id="np2" className="input" type="password" autoComplete="new-password" value={newPw2} onChange={(e) => setNewPw2(e.target.value)} />
          <button className="btn btn-primary full" disabled={busy}>Enregistrer</button>
        </form>

        <div className="card empty">
          <h2>Supprimer mon compte</h2>
          <p className="muted small">Supprime définitivement votre compte et tout votre historique. Cette action est irréversible.</p>
          <label className="label" htmlFor="del">Tapez SUPPRIMER pour confirmer</label>
          <input id="del" className="input" value={delText} onChange={(e) => setDelText(e.target.value)} />
          <button className="btn full danger" disabled={busy} onClick={deleteAccount}>Supprimer définitivement</button>
        </div>

        {error && <p className="error" role="alert">{error}</p>}
        {info && <p className="info" role="status">{info}</p>}
      </>
    );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null); setInfo(null);
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Adresse email invalide.");
    if (mode === "forgot") {
      setBusy(true);
      const { error } = await sb!.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/compte` });
      setBusy(false);
      if (error) return setError(authErrorFr(error.message));
      return setInfo("Si un compte existe pour cet email, un lien pour choisir un nouveau mot de passe vient d'être envoyé.");
    }
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
          <button key={m} type="button" role="tab" aria-selected={mode === m || (m === "login" && mode === "forgot")}
            className={mode === m || (m === "login" && mode === "forgot") ? "tab active" : "tab"} onClick={() => { setMode(m); setError(null); setInfo(null); }}>
            {m === "login" ? "Connexion" : "Inscription"}
          </button>
        ))}
      </div>
      <label className="label" htmlFor="email">Email</label>
      <input id="email" className="input" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      {mode !== "forgot" && (
        <>
          <label className="label" htmlFor="pw">Mot de passe</label>
          <input id="pw" className="input" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </>
      )}
      {mode === "signup" && (
        <>
          <label className="label" htmlFor="pw2">Confirmer le mot de passe</label>
          <input id="pw2" className="input" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      {info && <p className="info" role="status">{info}</p>}
      <button className="btn btn-primary full" disabled={busy}>
        {busy ? "Patientez…" : mode === "login" ? "Se connecter" : mode === "signup" ? "Créer mon compte" : "Recevoir le lien"}
      </button>
      {mode === "login" && (
        <button type="button" className="linkbtn" onClick={() => { setMode("forgot"); setError(null); setInfo(null); }}>
          Mot de passe oublié ?
        </button>
      )}
      {mode === "forgot" && (
        <button type="button" className="linkbtn" onClick={() => { setMode("login"); setError(null); setInfo(null); }}>
          Retour à la connexion
        </button>
      )}
      <p className="muted small center">Le compte est facultatif : l&apos;analyse reste possible sans compte.</p>
    </form>
  );
}
