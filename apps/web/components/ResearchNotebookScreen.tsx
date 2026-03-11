"use client";

import { useMemo, useState } from "react";

import {
  createResearchNote,
  createThesis,
  deleteResearchNote,
  deleteThesis,
  getNoteSynthesis,
  getResearchQa,
  getResearchNotes,
  getResearchTheses,
  updateResearchNote,
  updateThesis
} from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/format";
import type { NoteSynthesis, ResearchNote, ResearchQaResponse, Thesis } from "@/lib/types";
import { StateNotice } from "@/components/StateNotice";

interface ResearchNotebookScreenProps {
  initialNotes: ResearchNote[];
  initialTheses: Thesis[];
  initialThemes: string[];
  initialSynthesis: NoteSynthesis;
}

interface NoteDraft {
  id: string | null;
  symbol: string;
  title: string;
  content: string;
  note_type: string;
  theme: string;
  sector: string;
  event_ref: string;
}

interface ThesisDraft {
  id: string | null;
  symbol: string;
  title: string;
  status: string;
  summary: string;
}

const NOTE_TYPES = ["thesis", "risk", "catalyst", "post_mortem", "journal"];
const THESIS_STATUSES = ["active", "watch", "archived"];

export function ResearchNotebookScreen({
  initialNotes,
  initialTheses,
  initialThemes,
  initialSynthesis
}: ResearchNotebookScreenProps) {
  const [notes, setNotes] = useState(initialNotes);
  const [theses, setTheses] = useState(initialTheses);
  const [themes] = useState(initialThemes);
  const [synthesis, setSynthesis] = useState(initialSynthesis);

  const [query, setQuery] = useState("");
  const [filterSymbol, setFilterSymbol] = useState(initialSynthesis.scope_symbol ?? "AAPL");
  const [filterTheme, setFilterTheme] = useState(initialSynthesis.scope_theme ?? "");
  const [filterType, setFilterType] = useState("");

  const [noteDraft, setNoteDraft] = useState<NoteDraft>({
    id: null,
    symbol: initialSynthesis.scope_symbol ?? "AAPL",
    title: "",
    content: "",
    note_type: "thesis",
    theme: initialSynthesis.scope_theme ?? "",
    sector: "",
    event_ref: ""
  });

  const [thesisDraft, setThesisDraft] = useState<ThesisDraft>({
    id: null,
    symbol: initialSynthesis.scope_symbol ?? "AAPL",
    title: "",
    status: "active",
    summary: ""
  });

  const [isSavingNote, setIsSavingNote] = useState(false);
  const [isSavingThesis, setIsSavingThesis] = useState(false);
  const [qaQuestion, setQaQuestion] = useState("What are the key risks right now?");
  const [qaResponse, setQaResponse] = useState<ResearchQaResponse | null>(null);
  const [isAskingQa, setIsAskingQa] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);

  const symbolOptions = useMemo(() => {
    const symbols = new Set<string>(["AAPL", "MSFT", "NVDA"]);
    notes.forEach((note) => {
      if (note.symbol) {
        symbols.add(note.symbol);
      }
    });
    theses.forEach((thesis) => {
      if (thesis.symbol) {
        symbols.add(thesis.symbol);
      }
    });
    return Array.from(symbols).sort();
  }, [notes, theses]);

  async function refreshNotebook() {
    const [nextNotes, nextTheses] = await Promise.all([
      getResearchNotes({
        q: query || undefined,
        symbol: filterSymbol || undefined,
        note_type: filterType || undefined,
        theme: filterTheme || undefined,
        limit: 150
      }),
      getResearchTheses(filterSymbol || undefined)
    ]);

    setNotes(nextNotes);
    setTheses(nextTheses);
  }

  async function refreshSynthesis() {
    const scopeSymbol = filterSymbol || notes[0]?.symbol || "AAPL";
    const payload = await getNoteSynthesis({
      symbol: scopeSymbol || undefined,
      theme: filterTheme || undefined
    });
    setSynthesis(payload);
  }

  async function askQa() {
    const question = qaQuestion.trim();
    if (question.length < 3) {
      setQaError("Question must be at least 3 characters.");
      return;
    }

    setIsAskingQa(true);
    try {
      const response = await getResearchQa({
        question,
        symbol: filterSymbol || undefined,
        limit: 6
      });
      setQaResponse(response);
      setQaError(null);
    } catch {
      setQaError("Unable to answer question from current note/filing corpus.");
    } finally {
      setIsAskingQa(false);
    }
  }

  async function saveNote() {
    if (!noteDraft.title.trim() || !noteDraft.content.trim()) {
      return;
    }
    setIsSavingNote(true);

    const payload = {
      symbol: noteDraft.symbol || null,
      title: noteDraft.title,
      content: noteDraft.content,
      note_type: noteDraft.note_type,
      theme: noteDraft.theme || null,
      sector: noteDraft.sector || null,
      event_ref: noteDraft.event_ref || null
    };

    if (noteDraft.id) {
      await updateResearchNote(noteDraft.id, payload);
    } else {
      await createResearchNote(payload);
    }

    setNoteDraft((current) => ({
      ...current,
      id: null,
      title: "",
      content: "",
      event_ref: ""
    }));

    await refreshNotebook();
    await refreshSynthesis();
    setIsSavingNote(false);
  }

  async function removeNote(noteId: string) {
    await deleteResearchNote(noteId);
    await refreshNotebook();
    await refreshSynthesis();
  }

  async function saveThesis() {
    if (!thesisDraft.title.trim() || !thesisDraft.summary.trim()) {
      return;
    }
    setIsSavingThesis(true);

    const payload = {
      symbol: thesisDraft.symbol || null,
      title: thesisDraft.title,
      status: thesisDraft.status,
      summary: thesisDraft.summary
    };

    if (thesisDraft.id) {
      await updateThesis(thesisDraft.id, payload);
    } else {
      await createThesis(payload);
    }

    setThesisDraft((current) => ({
      ...current,
      id: null,
      title: "",
      summary: ""
    }));

    await refreshNotebook();
    await refreshSynthesis();
    setIsSavingThesis(false);
  }

  async function removeThesis(thesisId: string) {
    await deleteThesis(thesisId);
    await refreshNotebook();
    await refreshSynthesis();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Research</p>
          <h2 className="text-2xl font-semibold text-textPrimary">Research Notebook</h2>
        </div>

        <div className="ml-auto grid gap-2 md:grid-cols-5">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search notes"
            className="rounded-md border border-border bg-panel px-3 py-2 text-sm text-textPrimary"
          />
          <select
            value={filterSymbol}
            onChange={(event) => setFilterSymbol(event.target.value)}
            className="rounded-md border border-border bg-panel px-2 py-2 text-sm text-textPrimary"
          >
            {symbolOptions.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
          <select
            value={filterType}
            onChange={(event) => setFilterType(event.target.value)}
            className="rounded-md border border-border bg-panel px-2 py-2 text-sm text-textPrimary"
          >
            <option value="">All note types</option>
            {NOTE_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={filterTheme}
            onChange={(event) => setFilterTheme(event.target.value)}
            className="rounded-md border border-border bg-panel px-2 py-2 text-sm text-textPrimary"
          >
            <option value="">All themes</option>
            {themes.map((theme) => (
              <option key={theme} value={theme}>
                {theme}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => {
              void refreshNotebook();
              void refreshSynthesis();
            }}
            className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-[#06121e]"
          >
            Apply Filters
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr,1fr]">
        <section className="panel">
          <div className="panel-header flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">Notes</h3>
              <p className="text-xs text-textSecondary">{notes.length} notes in current scope</p>
            </div>
          </div>
          <div className="panel-body space-y-3">
            {notes.map((note) => (
              <article key={note.id} className="rounded-lg border border-border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-textPrimary">{note.title}</p>
                  <div className="flex gap-2">
                    <span className="rounded border border-border px-2 py-1 text-xs text-textSecondary">
                      {note.symbol ?? "GLOBAL"}
                    </span>
                    <span className="rounded border border-border px-2 py-1 text-xs text-textSecondary">
                      {note.note_type}
                    </span>
                  </div>
                </div>
                <p className="mt-2 text-sm text-textSecondary">{note.content}</p>
                <p className="mt-2 text-xs text-textSecondary">Updated {formatDateTime(note.updated_at)}</p>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setNoteDraft({
                        id: note.id,
                        symbol: note.symbol ?? "",
                        title: note.title,
                        content: note.content,
                        note_type: note.note_type,
                        theme: note.theme ?? "",
                        sector: note.sector ?? "",
                        event_ref: note.event_ref ?? ""
                      });
                    }}
                    className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      void removeNote(note.id);
                    }}
                    className="rounded border border-danger/50 px-2 py-1 text-xs text-danger"
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <div className="space-y-6">
          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold text-textPrimary">
                {noteDraft.id ? "Edit Note" : "Create Note"}
              </h3>
            </div>
            <div className="panel-body grid gap-2">
              <input
                value={noteDraft.title}
                onChange={(event) => setNoteDraft((draft) => ({ ...draft, title: event.target.value }))}
                placeholder="Title"
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={noteDraft.symbol}
                  onChange={(event) => setNoteDraft((draft) => ({ ...draft, symbol: event.target.value }))}
                  className="rounded-md border border-border bg-panelMuted px-2 py-2 text-sm text-textPrimary"
                >
                  <option value="">GLOBAL</option>
                  {symbolOptions.map((symbol) => (
                    <option key={symbol} value={symbol}>
                      {symbol}
                    </option>
                  ))}
                </select>
                <select
                  value={noteDraft.note_type}
                  onChange={(event) =>
                    setNoteDraft((draft) => ({ ...draft, note_type: event.target.value }))
                  }
                  className="rounded-md border border-border bg-panelMuted px-2 py-2 text-sm text-textPrimary"
                >
                  {NOTE_TYPES.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  value={noteDraft.theme}
                  onChange={(event) => setNoteDraft((draft) => ({ ...draft, theme: event.target.value }))}
                  placeholder="Theme"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
                <input
                  value={noteDraft.event_ref}
                  onChange={(event) =>
                    setNoteDraft((draft) => ({ ...draft, event_ref: event.target.value }))
                  }
                  placeholder="Event ref"
                  className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                />
              </div>
              <textarea
                value={noteDraft.content}
                onChange={(event) => setNoteDraft((draft) => ({ ...draft, content: event.target.value }))}
                placeholder="Write note"
                rows={6}
                className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    void saveNote();
                  }}
                  className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-[#06121e]"
                >
                  {isSavingNote ? "Saving..." : noteDraft.id ? "Update Note" : "Create Note"}
                </button>
                {noteDraft.id ? (
                  <button
                    type="button"
                    onClick={() =>
                      setNoteDraft((current) => ({
                        ...current,
                        id: null,
                        title: "",
                        content: "",
                        event_ref: ""
                      }))
                    }
                    className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary"
                  >
                    Cancel Edit
                  </button>
                ) : null}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header flex items-center justify-between">
              <h3 className="text-sm font-semibold text-textPrimary">Theses</h3>
              <span className="text-xs text-textSecondary">{theses.length} entries</span>
            </div>
            <div className="panel-body space-y-3">
              {theses.map((thesis) => (
                <article key={thesis.id} className="rounded-md border border-border p-3">
                  <p className="text-sm font-medium text-textPrimary">{thesis.title}</p>
                  <p className="mt-1 text-xs text-textSecondary">
                    {thesis.symbol ?? "GLOBAL"} · {thesis.status} · {formatDate(thesis.updated_at)}
                  </p>
                  <p className="mt-2 text-sm text-textSecondary">{thesis.summary}</p>
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        setThesisDraft({
                          id: thesis.id,
                          symbol: thesis.symbol ?? "",
                          title: thesis.title,
                          status: thesis.status,
                          summary: thesis.summary
                        })
                      }
                      className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void removeThesis(thesis.id);
                      }}
                      className="rounded border border-danger/50 px-2 py-1 text-xs text-danger"
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}

              <div className="rounded-md border border-border p-3">
                <p className="mb-2 text-xs uppercase tracking-wider text-textSecondary">
                  {thesisDraft.id ? "Edit Thesis" : "Create Thesis"}
                </p>
                <div className="grid gap-2">
                  <input
                    value={thesisDraft.title}
                    onChange={(event) =>
                      setThesisDraft((draft) => ({ ...draft, title: event.target.value }))
                    }
                    placeholder="Thesis title"
                    className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={thesisDraft.symbol}
                      onChange={(event) =>
                        setThesisDraft((draft) => ({ ...draft, symbol: event.target.value }))
                      }
                      className="rounded-md border border-border bg-panelMuted px-2 py-2 text-sm text-textPrimary"
                    >
                      <option value="">GLOBAL</option>
                      {symbolOptions.map((symbol) => (
                        <option key={symbol} value={symbol}>
                          {symbol}
                        </option>
                      ))}
                    </select>
                    <select
                      value={thesisDraft.status}
                      onChange={(event) =>
                        setThesisDraft((draft) => ({ ...draft, status: event.target.value }))
                      }
                      className="rounded-md border border-border bg-panelMuted px-2 py-2 text-sm text-textPrimary"
                    >
                      {THESIS_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </div>
                  <textarea
                    value={thesisDraft.summary}
                    onChange={(event) =>
                      setThesisDraft((draft) => ({ ...draft, summary: event.target.value }))
                    }
                    rows={4}
                    placeholder="Thesis summary"
                    className="rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      void saveThesis();
                    }}
                    className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-[#06121e]"
                  >
                    {isSavingThesis ? "Saving..." : thesisDraft.id ? "Update Thesis" : "Create Thesis"}
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-textPrimary">AI Note Synthesis</h3>
                <p className="text-xs text-textSecondary">
                  {synthesis.source_model} · generated {formatDateTime(synthesis.generated_at)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  void refreshSynthesis();
                }}
                className="rounded border border-border px-2 py-1 text-xs text-textSecondary"
              >
                Refresh
              </button>
            </div>
            <div className="panel-body space-y-3 text-sm text-textSecondary">
              <p>{synthesis.synthesized_thesis}</p>
              <div>
                <p className="kpi-label">Open Questions</p>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {synthesis.open_questions.map((item, index) => (
                    <li key={`question-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="kpi-label">Risks</p>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {synthesis.risks.map((item, index) => (
                    <li key={`risk-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="kpi-label">Next Things To Watch</p>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {synthesis.next_watch.map((item, index) => (
                    <li key={`watch-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold text-textPrimary">Ask Notes + Filings</h3>
              <p className="text-xs text-textSecondary">
                Citation-backed retrieval over your research corpus.
              </p>
            </div>
            <div className="panel-body space-y-3">
              <textarea
                value={qaQuestion}
                onChange={(event) => setQaQuestion(event.target.value)}
                rows={3}
                placeholder="Ask a question about current thesis, risk, or filing changes..."
                className="w-full rounded-md border border-border bg-panelMuted px-3 py-2 text-sm text-textPrimary"
              />
              <button
                type="button"
                onClick={() => {
                  void askQa();
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary hover:text-textPrimary"
                disabled={isAskingQa}
              >
                {isAskingQa ? "Querying..." : "Ask"}
              </button>

              {qaError ? <StateNotice tone="error" title={qaError} /> : null}

              {qaResponse ? (
                <div className="space-y-3 rounded-md border border-border px-3 py-3">
                  <p className="text-xs text-textSecondary">
                    {qaResponse.source_model} · {qaResponse.coverage_count} citations
                  </p>
                  <pre className="whitespace-pre-wrap text-sm text-textPrimary">{qaResponse.answer}</pre>
                  <div className="space-y-2">
                    {qaResponse.citations.map((citation) => (
                      <article key={citation.source_id} className="rounded-md border border-border px-3 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs text-textPrimary">{citation.title}</p>
                          <p className="text-xs text-textSecondary">{citation.source_type}</p>
                        </div>
                        <p className="mt-1 text-xs text-textSecondary">{citation.snippet}</p>
                        <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-textSecondary">
                          <span>Score {citation.score.toFixed(2)}</span>
                          <span>{formatDate(citation.as_of)}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ) : (
                <StateNotice
                  title="No QA response yet."
                  detail="Ask a question to retrieve the highest-signal notes and filings with citations."
                />
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
