// HIER TRAGST DU DEINE RAILWAY API URL EIN, zB: https://xyz.up.railway.app
const API_BASE = "https://tbc-recruit.onrender.com";

const CLASSES = {
  "Warrior": ["Arms", "Fury", "Protection"],
  "Paladin": ["Holy", "Protection", "Retribution"],
  "Hunter": ["Beast Mastery", "Marksmanship", "Survival"],
  "Rogue": ["Assassination", "Combat", "Subtlety"],
  "Priest": ["Discipline", "Holy", "Shadow"],
  "Shaman": ["Elemental", "Enhancement", "Restoration"],
  "Mage": ["Arcane", "Fire", "Frost"],
  "Warlock": ["Affliction", "Demonology", "Destruction"],
  "Druid": ["Balance", "Feral", "Restoration"],
};

const DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
const ATTUNES = ["Karazhan","SSC","TK","Hyjal","BT"];

function qs(id) { return document.getElementById(id); }
function el(tag, cls) { const e = document.createElement(tag); if (cls) e.className = cls; return e; }

function fillClassSelect(selectEl, includeAny=true) {
  selectEl.innerHTML = "";
  if (includeAny) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Klasse egal";
    selectEl.appendChild(opt);
  }
  Object.keys(CLASSES).forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    selectEl.appendChild(opt);
  });
}

function fillSpecSelect(classSelect, specSelect, includeAny=true) {
  const c = classSelect.value || Object.keys(CLASSES)[0];
  specSelect.innerHTML = "";
  if (includeAny) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Spec egal";
    specSelect.appendChild(opt);
  }
  (CLASSES[c] || []).forEach(s => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    specSelect.appendChild(opt);
  });
}

function createChips(container, items) {
  container.innerHTML = "";
  items.forEach(x => {
    const c = el("div", "chip");
    c.textContent = x;
    c.addEventListener("click", () => c.classList.toggle("on"));
    container.appendChild(c);
  });
}

function getChipsOn(container) {
  return [...container.querySelectorAll(".chip.on")].map(x => x.textContent);
}

function parseProgress(text) {
  const out = {};
  (text || "")
    .split(";")
    .map(s => s.trim())
    .filter(Boolean)
    .forEach(pair => {
      const idx = pair.indexOf("=");
      if (idx > 0) {
        const k = pair.slice(0, idx).trim();
        const v = pair.slice(idx + 1).trim();
        if (k && v) out[k] = v;
      }
    });
  return out;
}

async function apiGet(path, params={}) {
  const url = new URL(API_BASE + path);
  Object.entries(params).forEach(([k,v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function apiPost(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

function renderGuild(g) {
  const d = el("div", "result");
  const h = el("h4");
  h.textContent = `${g.name} (${g.realm})`;
  d.appendChild(h);

  const meta = el("div", "meta");
  meta.textContent = `${g.faction} | ${g.language} | ${g.raid_days.join(", ")} ${g.raid_time_start}-${g.raid_time_end} | Loot: ${g.loot_system}`;
  d.appendChild(meta);

  const pills = el("div");
  Object.keys(g.progress || {}).forEach(k => {
    const p = el("span", "pill");
    p.textContent = `${k} ${g.progress[k]}`;
    pills.appendChild(p);
  });
  (g.needs || []).forEach(n => {
    const cls = n.class || n.class_name || "";
    const spec = n.spec || "";
    const role = n.role || "";
    const prio = n.prio ?? "";
    const p = el("span", "pill");
    p.textContent = `Need: ${cls}${spec ? " " + spec : ""} (${role}) Prio ${prio}`;
    pills.appendChild(p);
  });
  d.appendChild(pills);

  if (g.description) {
    const t = el("div", "meta");
    t.textContent = g.description;
    d.appendChild(t);
  }

  const actions = el("div", "row");
  if (g.contact_character) {
    const p = el("span", "pill");
    p.textContent = `Kontakt: ${g.contact_character}`;
    actions.appendChild(p);
  }
  if (g.discord) {
    const a = document.createElement("a");
    a.href = g.discord;
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = "Discord";
    a.className = "pill";
    actions.appendChild(a);
  }
  if (g.website) {
    const a = document.createElement("a");
    a.href = g.website;
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = "Website";
    a.className = "pill";
    actions.appendChild(a);
  }
  d.appendChild(actions);

  return d;
}

function renderPlayer(p) {
  const d = el("div", "result");
  const h = el("h4");
  h.textContent = `${p.name} (${p.realm})`;
  d.appendChild(h);

  const meta = el("div", "meta");
  meta.textContent = `${p.faction} | ${p.language} | ${p.class_name} ${p.spec} | Rolle: ${p.role} | Skill: ${p.skill_rating}/5`;
  d.appendChild(meta);

  const pills = el("div");
  (p.professions || []).forEach(x => {
    const pi = el("span", "pill");
    pi.textContent = x;
    pills.appendChild(pi);
  });
  (p.attunements || []).forEach(x => {
    const pi = el("span", "pill");
    pi.textContent = `Attune: ${x}`;
    pills.appendChild(pi);
  });
  (p.availability || []).forEach(x => {
    const pi = el("span", "pill");
    pi.textContent = `Avail: ${x}`;
    pills.appendChild(pi);
  });
  d.appendChild(pills);

  if (p.note) {
    const t = el("div", "meta");
    t.textContent = p.note;
    d.appendChild(t);
  }

  if (p.logs_url) {
    const a = document.createElement("a");
    a.href = p.logs_url;
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = "Logs";
    a.className = "pill";
    d.appendChild(a);
  }

  return d;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
      document.querySelectorAll(".panel").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      qs(btn.dataset.tab).classList.add("active");
    });
  });
}

function setupUI() {
  qs("apiHint").textContent = `API: ${API_BASE}`;

  fillClassSelect(qs("gNeedClass"), true);
  fillClassSelect(qs("pClass"), true);
  qs("pClass").addEventListener("change", () => fillSpecSelect(qs("pClass"), qs("pSpec"), true));
  fillSpecSelect(qs("pClass"), qs("pSpec"), true);

  fillClassSelect(qs("ngNeedClass"), false);
  fillSpecSelect(qs("ngNeedClass"), qs("ngNeedSpec"), false);
  qs("ngNeedClass").addEventListener("change", () => fillSpecSelect(qs("ngNeedClass"), qs("ngNeedSpec"), false));

  fillClassSelect(qs("npClass"), false);
  fillSpecSelect(qs("npClass"), qs("npSpec"), false);
  qs("npClass").addEventListener("change", () => fillSpecSelect(qs("npClass"), qs("npSpec"), false));

  createChips(qs("ngDays"), DAYS);
  createChips(qs("npDays"), DAYS);
  createChips(qs("npAttunes"), ATTUNES);
}

function setupActions() {
  qs("loadGuilds").addEventListener("click", async () => {
    const params = {
      realm: qs("gRealm").value.trim(),
      faction: qs("gFaction").value,
      language: qs("gLang").value,
      q: qs("gQuery").value.trim(),
      need_class: qs("gNeedClass").value,
      need_role: qs("gNeedRole").value,
    };
    qs("guildResults").textContent = "Lade...";
    try {
      const data = await apiGet("/api/guilds", params);
      qs("guildResults").innerHTML = "";
      if (!data.length) qs("guildResults").textContent = "Keine Treffer.";
      data.forEach(g => qs("guildResults").appendChild(renderGuild(g)));
    } catch (e) {
      qs("guildResults").textContent = "Fehler: " + e.message;
    }
  });

  qs("loadPlayers").addEventListener("click", async () => {
    const params = {
      realm: qs("pRealm").value.trim(),
      faction: qs("pFaction").value,
      language: qs("pLang").value,
      q: qs("pQuery").value.trim(),
      class_name: qs("pClass").value,
      spec: qs("pSpec").value,
      role: qs("pRole").value,
      min_skill: qs("pMinSkill").value,
    };
    qs("playerResults").textContent = "Lade...";
    try {
      const data = await apiGet("/api/players", params);
      qs("playerResults").innerHTML = "";
      if (!data.length) qs("playerResults").textContent = "Keine Treffer.";
      data.forEach(p => qs("playerResults").appendChild(renderPlayer(p)));
    } catch (e) {
      qs("playerResults").textContent = "Fehler: " + e.message;
    }
  });

  const needs = [];
  function renderNeeds() {
    const box = qs("ngNeedsList");
    box.innerHTML = "";
    if (!needs.length) {
      box.textContent = "Noch keine Needs hinzugefuegt.";
      return;
    }
    needs.forEach((n, idx) => {
      const row = el("div", "result");
      const title = el("div", "meta");
      title.textContent = `${n.class} ${n.spec} | ${n.role} | Prio ${n.prio}`;
      row.appendChild(title);

      const del = el("button");
      del.textContent = "Entfernen";
      del.addEventListener("click", () => {
        needs.splice(idx, 1);
        renderNeeds();
      });
      row.appendChild(del);
      box.appendChild(row);
    });
  }

  qs("ngAddNeed").addEventListener("click", () => {
    needs.push({
      class: qs("ngNeedClass").value,
      spec: qs("ngNeedSpec").value,
      role: qs("ngNeedRole").value,
      prio: Number(qs("ngNeedPrio").value),
    });
    renderNeeds();
  });
  renderNeeds();

  qs("createGuild").addEventListener("click", async () => {
    const body = {
      name: qs("ngName").value.trim(),
      realm: qs("ngRealm").value.trim(),
      faction: qs("ngFaction").value,
      language: qs("ngLang").value,
      raid_days: getChipsOn(qs("ngDays")),
      raid_time_start: qs("ngStart").value.trim(),
      raid_time_end: qs("ngEnd").value.trim(),
      progress: parseProgress(qs("ngProgress").value),
      needs: needs,
      loot_system: qs("ngLoot").value.trim(),
      contact_character: qs("ngContact").value.trim(),
      discord: qs("ngDiscord").value.trim(),
      website: qs("ngWebsite").value.trim(),
      description: qs("ngDesc").value.trim(),
    };
    qs("guildCreated").textContent = "Speichere...";
    try {
      const data = await apiPost("/api/guilds", body);
      qs("guildCreated").textContent =
        "Gilde gespeichert.\n" +
        "Guild ID: " + data.guild.id + "\n" +
        "Edit Token: " + data.edit_token + "\n" +
        "Wichtig: Token speichern, sonst kannst du spaeter nicht editieren.";
    } catch (e) {
      qs("guildCreated").textContent = "Fehler: " + e.message;
    }
  });

  qs("createPlayer").addEventListener("click", async () => {
    const profs = (qs("npProf").value || "")
      .split(",")
      .map(x => x.trim())
      .filter(Boolean);

    const body = {
      name: qs("npName").value.trim(),
      realm: qs("npRealm").value.trim(),
      faction: qs("npFaction").value,
      language: qs("npLang").value,
      class_name: qs("npClass").value,
      spec: qs("npSpec").value,
      role: qs("npRole").value,
      skill_rating: Number(qs("npSkill").value),
      professions: profs,
      attunements: getChipsOn(qs("npAttunes")),
      availability: getChipsOn(qs("npDays")),
      logs_url: qs("npLogs").value.trim(),
      note: qs("npNote").value.trim(),
    };

    qs("playerCreated").textContent = "Speichere...";
    try {
      const data = await apiPost("/api/players", body);
      qs("playerCreated").textContent =
        "Profil gespeichert.\n" +
        "Player ID: " + data.player.id + "\n" +
        "Edit Token: " + data.edit_token + "\n";
    } catch (e) {
      qs("playerCreated").textContent = "Fehler: " + e.message;
    }
  });
}

setupTabs();
setupUI();
setupActions();
