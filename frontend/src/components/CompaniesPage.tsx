import { useRef, useState } from "react";
import { api } from "../api";
import type { Company } from "../types";

interface Props {
  companies: Company[];
  refresh: () => void;
}

export default function CompaniesPage({ companies, refresh }: Props) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const add = async () => {
    if (!name.trim()) return;
    setMessage("Adding + detecting ATS…");
    try {
      const c = await api.addCompany(name.trim(), url.trim());
      setMessage(c.ats_type !== "unknown" ? `Added ${c.name} — detected ${c.ats_type} (${c.ats_identifier})` : `Added ${c.name} — ATS not detected, set it manually or retry Detect`);
      setName(""); setUrl("");
      refresh();
    } catch (e) { setMessage(String(e)); }
  };

  const importCsv = async (f: File) => {
    setMessage("Importing CSV…");
    try {
      const r = await api.importCsv(f);
      setMessage(`Imported ${r.added} companies (${r.skipped_existing} already existed)`);
      refresh();
    } catch (e) { setMessage(String(e)); }
  };

  const act = async (id: number, fn: () => Promise<unknown>, done: string) => {
    setBusy(id);
    try { await fn(); setMessage(done); refresh(); }
    catch (e) { setMessage(String(e)); }
    finally { setBusy(null); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-surface border border-line rounded-lg p-4 flex items-end gap-3 flex-wrap">
        <div>
          <label className="text-[11px] uppercase tracking-wide text-muted font-medium block mb-1">Company name</label>
          <input className="bg-paper border border-line rounded-md px-2 py-1.5 text-sm w-52" value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Corp" />
        </div>
        <div className="flex-1 min-w-64">
          <label className="text-[11px] uppercase tracking-wide text-muted font-medium block mb-1">Careers URL</label>
          <input className="bg-paper border border-line rounded-md px-2 py-1.5 text-sm w-full" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://acme.com/careers" />
        </div>
        <button className="btn-primary !px-4 !py-2 !text-sm" onClick={add}>Add company</button>
        <button className="btn-ghost !px-4 !py-2 !text-sm" onClick={() => fileRef.current?.click()}>Import CSV</button>
        <input ref={fileRef} type="file" accept=".csv" className="hidden"
               onChange={(e) => e.target.files?.[0] && importCsv(e.target.files[0])} />
        <span className="text-xs text-muted w-full">CSV columns: name, careers_url — ATS type and board token are auto-detected. {message}</span>
      </div>

      <table className="w-full bg-surface border border-line rounded-lg text-sm border-separate border-spacing-0 overflow-hidden">
        <thead className="bg-paper">
          <tr>
            {["Company", "ATS", "Board ID", "Jobs", "Interval", "Last checked", "Status", ""].map((h) => (
              <th key={h} className="text-left text-[11px] uppercase tracking-wide text-muted font-medium px-3 py-2">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr key={c.id} className={`border-t border-line ${!c.enabled ? "opacity-50" : ""}`}>
              <td className="px-3 py-2 font-medium border-t border-line">{c.name}</td>
              <td className="px-3 py-2 capitalize text-muted border-t border-line">{c.ats_type}</td>
              <td className="px-3 py-2 font-mono text-xs text-muted border-t border-line">{c.ats_identifier || "—"}</td>
              <td className="px-3 py-2 font-mono text-xs border-t border-line">{c.job_count}</td>
              <td className="px-3 py-2 font-mono text-xs text-muted border-t border-line">{c.poll_interval_seconds}s</td>
              <td className="px-3 py-2 font-mono text-xs text-muted whitespace-nowrap border-t border-line">
                {c.last_checked_at ? new Date(c.last_checked_at).toLocaleTimeString() : "never"}
              </td>
              <td className={`px-3 py-2 text-xs max-w-64 truncate border-t border-line ${c.last_status.startsWith("error") ? "text-hot" : "text-muted"}`} title={c.last_status}>
                {c.last_status}
              </td>
              <td className="px-3 py-2 whitespace-nowrap border-t border-line">
                <button className="btn-ghost mr-1" disabled={busy === c.id}
                        onClick={() => act(c.id, () => api.pollCompany(c.id), `Polled ${c.name}`)}>
                  {busy === c.id ? "…" : "Poll now"}
                </button>
                <button className="btn-ghost" disabled={busy === c.id}
                        onClick={() => act(c.id, () => api.detectCompany(c.id), `Re-detected ATS for ${c.name}`)}>
                  Detect
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
