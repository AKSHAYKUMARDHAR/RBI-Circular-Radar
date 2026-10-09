"use strict";

const GROUPS = [
  ["Banks", ["commercial_banks", "small_finance_banks", "payments_banks", "regional_rural_banks", "local_area_banks",
             "urban_coop_banks", "rural_coop_banks"]],
  ["NBFCs and institutions", ["nbfcs", "aifis", "arcs", "cics"]],
  ["Payments", ["payment_aggregators", "ppi_issuers", "payment_operators"]],
  ["Foreign exchange and markets", ["authorised_dealers", "primary_dealers", "other"]],
];
const SHORT = {
  commercial_banks: "Commercial banks", small_finance_banks: "Small finance banks", payments_banks: "Payments banks",
  regional_rural_banks: "Regional rural banks", local_area_banks: "Local area banks",
  urban_coop_banks: "Urban co-op banks", rural_coop_banks: "Rural co-op banks", nbfcs: "NBFCs and HFCs",
  aifis: "All-India FIs", arcs: "ARCs", cics: "Credit info companies", payment_aggregators: "Payment aggregators",
  ppi_issuers: "PPI issuers", payment_operators: "Other payment operators", authorised_dealers: "Authorised dealers",
  primary_dealers: "Primary dealers", other: "Others addressed",
};
const KIND = {
  new_direction: "New direction", amendment: "Amendment", withdrawal: "Withdrawal", draft: "Draft for comments",
  rates_operational: "Rates and operations", clarification: "Clarification", other: "Other",
};
const KEY = "rbi-radar.profile.v1";
const $ = (s) => document.querySelector(s);

let all = [];
let profile = new Set(loadProfile());

function loadProfile() {
  try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; }
}
function saveProfile() {
  try { localStorage.setItem(KEY, JSON.stringify([...profile])); } catch { /* private window: profile lasts this visit */ }
}

function fmtDate(iso) {
  if (!iso || !/^\d{4}-\d\d-\d\d$/.test(iso)) return iso || "";
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v; else if (k === "text") n.textContent = v; else n.setAttribute(k, v);
  }
  for (const k of kids) if (k != null) n.append(k);
  return n;
}

function evidence(rec, ev) {
  // "quote, p. N" toggle with the exact words and a link to that page of RBI's PDF
  if (!ev || !ev.quote) return null;
  const d = el("details");
  d.append(el("summary", { text: ev.page ? `quote, p. ${ev.page}` : "quote" }));
  const q = el("span", { class: "quote" }, `“${ev.quote}” `);
  if (ev.page) q.append(el("a", { href: `${rec.pdf}#page=${ev.page}`, target: "_blank", rel: "noopener", text: `PDF p. ${ev.page}` }));
  d.append(q);
  return d;
}

function dateLine(rec, d, emptyText) {
  const dd = el("dd");
  if (!d || d.status === "not_stated" || d.status === "none" || d.value === "not_stated" || d.value === "none") {
    dd.textContent = emptyText;
    return dd;
  }
  if (d.status === "check") {
    dd.append(el("span", { class: "badge check", text: "check the document" }));
    if (d.note) dd.append(el("span", { class: "note", text: d.note }));
  } else {
    dd.append(document.createTextNode(fmtDate(d.value)));
  }
  dd.append(evidence(rec, d) || "");
  return dd;
}

function matches(rec) {
  if (!profile.size) return "all";
  const hit = rec.applies_to.filter((a) => profile.has(a.type));
  if (!hit.length) return null;
  return hit.some((a) => a.status !== "check") ? "yes" : "maybe";
}

function card(rec, match) {
  const c = $("#card").content.firstElementChild.cloneNode(true);
  if (match === "yes" || match === "maybe") c.classList.add("mine");
  c.querySelector(".date").textContent = fmtDate(rec.date);
  c.querySelector(".date").setAttribute("datetime", rec.date || "");
  c.querySelector(".kind").textContent = KIND[rec.kind] || "Unclassified";
  const act = c.querySelector(".act");
  act.textContent = rec.action_required === "yes" ? "Action required" : rec.action_required === "no" ? "No action" : "Action: check";
  if (rec.action_required === "yes") act.classList.add("yes");
  if (!rec.action_required) act.classList.add("check");
  const you = c.querySelector(".you");
  if (match === "yes") { you.hidden = false; you.textContent = "Applies to you"; }
  if (match === "maybe") { you.hidden = false; you.textContent = "May apply to you"; you.classList.add("check"); }
  const a = c.querySelector(".title");
  a.textContent = rec.title;
  a.href = rec.url;
  c.querySelector(".rbino").textContent = [rec.rbi_no, rec.pages ? `${rec.pages} page${rec.pages > 1 ? "s" : ""}` : null,
    rec.amends ? `amends ${rec.amends}` : null].filter(Boolean).join(" · ");
  const action = c.querySelector(".action");
  if (rec.action) {
    action.append(document.createTextNode(rec.action));
    action.append(evidence(rec, rec.action_evidence) || "");
  } else action.remove();
  const chips = c.querySelector(".chips");
  if (!rec.applies_to.length) chips.append(el("span", { class: "badge check", text: "not found: read the notification" }));
  for (const t of rec.applies_to) {
    const chip = el("span", { class: "chip" + (profile.has(t.type) ? " mine" : "") + (t.status === "check" ? " check" : ""),
                              text: (SHORT[t.type] || t.type) + (t.status === "check" ? "?" : "") });
    chip.title = t.status === "check" ? (t.note || "not confirmed: check") + (t.quote ? ` — “${t.quote}”` : "")
                                      : (t.quote ? `“${t.quote}”` + (t.page ? ` (p. ${t.page})` : "") : "");
    chips.append(chip);
  }
  const dl = c.querySelector(".dates");
  dl.append(el("dt", { text: "In force" }), dateLine(rec, rec.effective_date, "not stated"));
  const dd = el("dd");
  if (!rec.comply_by.length) dd.textContent = "none stated";
  rec.comply_by.forEach((x, i) => {
    const line = el("div");
    if (x.status === "check") line.append(el("span", { class: "badge check", text: `${fmtDate(x.value)}? check` }));
    else line.append(document.createTextNode(fmtDate(x.value)));
    if (x.what) line.append(document.createTextNode(` — ${x.what}`));
    line.append(evidence(rec, x) || "");
    if (x.status === "check" && x.note) line.append(el("span", { class: "note", text: x.note }));
    dd.append(line);
  });
  dl.append(el("dt", { text: "Deadlines" }), dd);
  if (rec.comments_by && rec.comments_by.value && rec.comments_by.value !== "none") {
    dl.append(el("dt", { text: "Comments by" }), dateLine(rec, rec.comments_by, "none"));
  }
  const r = rec.reader || {};
  c.querySelector(".src").textContent = r.rules_only
    ? "Read by rules only (the model was unavailable); it will be re-read on the next run."
    : `Read by rules and ${r.model}; every entity type and date checked against its quote.`;
  return c;
}

function visible() {
  const days = $("#period").value;
  const cutoff = days === "all" ? "" : new Date(Date.now() - Number(days) * 864e5).toISOString().slice(0, 10);
  const q = $("#q").value.trim().toLowerCase();
  const actionOnly = $("#action-only").checked;
  return all.map((r) => [r, matches(r)]).filter(([r, m]) =>
    m && (!cutoff || (r.date || "") >= cutoff) && (!q || r.title.toLowerCase().includes(q))
    && (!actionOnly || r.action_required === "yes"));
}

function render() {
  const list = $("#list");
  list.replaceChildren();
  const rows = visible();
  const who = profile.size ? `for ${[...profile].map((t) => SHORT[t]).join(", ")}` : "for all entity types";
  $("#count").textContent = `${rows.length} notification${rows.length === 1 ? "" : "s"} ${who}`;
  if (!rows.length) list.append(el("p", { class: "empty", text: "Nothing matches. Try a longer period or fewer filters." }));
  for (const [r, m] of rows) list.append(card(r, m));
}

function buildProfile(types) {
  const box = $("#profile");
  const known = new Set(types.map((t) => t.type));
  for (const [name, keys] of GROUPS) {
    const g = el("div");
    g.append(el("p", { class: "group-name", text: name }));
    const pick = el("div", { class: "pick" });
    for (const k of keys.filter((k) => known.has(k))) {
      const input = el("input", { type: "checkbox", value: k });
      input.checked = profile.has(k);
      input.addEventListener("change", () => {
        input.checked ? profile.add(k) : profile.delete(k);
        saveProfile();
        render();
      });
      const label = el("label", {}, input, SHORT[k]);
      label.title = (types.find((t) => t.type === k) || {}).label || "";
      pick.append(label);
    }
    g.append(pick);
    box.append(g);
  }
}

function csvCell(v) {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportCsv() {
  const head = ["date", "rbi_no", "title", "applies_to", "kind", "action_required", "action", "in_force",
                "deadlines", "comments_by", "url"];
  const dateCell = (d) => !d ? "" : d.status === "check" ? "check" : (d.value || "");
  const lines = [head.join(",")];
  for (const [r] of visible()) {
    lines.push([r.date, r.rbi_no, r.title,
      r.applies_to.map((a) => a.type + (a.status === "check" ? "?" : "")).join("; "),
      r.kind, r.action_required, r.action, dateCell(r.effective_date),
      r.comply_by.map((x) => x.value + (x.status === "check" ? "?" : "")).join("; "),
      dateCell(r.comments_by), r.url].map(csvCell).join(","));
  }
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = el("a", { href: URL.createObjectURL(blob), download: `rbi-radar-${new Date().toISOString().slice(0, 10)}.csv` });
  document.body.append(a);
  a.click();
  a.remove();
}

async function main() {
  try {
    const res = await fetch("data/notifications.json", { cache: "no-cache" });
    const data = await res.json();
    all = data.notifications;
    buildProfile(data.entity_types);
    const when = data.generated_at ? new Date(data.generated_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "";
    $("#meta").textContent = `${all.length} notifications read · last new one added ${when} · RBI checked every 10 minutes`;
    render();
  } catch (e) {
    $("#meta").textContent = "Couldn't load the digest. Try again in a minute.";
  }
  for (const id of ["#period", "#action-only"]) $(id).addEventListener("change", render);
  $("#q").addEventListener("input", render);
  $("#csv").addEventListener("click", exportCsv);
  $("#clear").addEventListener("click", () => {
    profile.clear();
    saveProfile();
    document.querySelectorAll("#profile input").forEach((i) => { i.checked = false; });
    render();
  });
}

main();
