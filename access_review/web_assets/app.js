const reviewForm = document.querySelector("#review-form");
const draftForm = document.querySelector("#draft-form");
const reviewSection = document.querySelector("#review");
const message = document.querySelector("#message");
const draftResult = document.querySelector("#draft-result");
let currentReview = null;
let reviewPayload = null;
let reviewGeneration = 0;

reviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();
  draftResult.hidden = true;
  currentReview = null;
  reviewPayload = null;
  reviewGeneration += 1;
  const generation = reviewGeneration;
  reviewSection.hidden = true;
  document.querySelector("#summary-result").hidden = true;
  document.querySelector("#summary-button").disabled = false;
  const button = reviewForm.querySelector("button[type='submit']");
  button.disabled = true;
  button.textContent = "Verifying manager…";
  try {
    const payload = basePayload();
    const report = await postJson("/api/review", payload);
    if (generation !== reviewGeneration) return;
    reviewPayload = payload;
    currentReview = report;
    renderReview(report);
    reviewSection.hidden = false;
    reviewSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    if (generation !== reviewGeneration) return;
    currentReview = null;
    reviewSection.hidden = true;
    showMessage(error.message);
  } finally {
    if (generation !== reviewGeneration) return;
    button.disabled = false;
    button.innerHTML = "Open access review <span aria-hidden='true'>→</span>";
  }
});

draftForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();
  if (!currentReview) return;
  const generation = reviewGeneration;
  const additions = selectedValues("addition");
  const removals = selectedValues("removal");
  if (!additions.length && !removals.length) {
    showMessage("Select at least one requested addition or removal.");
    return;
  }
  try {
    const response = await postJson("/api/service-desk-draft", {
      ...reviewPayload,
      additions,
      removals,
      reason: document.querySelector("#reason").value.trim(),
    });
    if (generation !== reviewGeneration) return;
    document.querySelector("#draft-text").textContent = response.draft;
    draftResult.hidden = false;
    draftResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    if (generation === reviewGeneration) showMessage(error.message);
  }
});

document.querySelector("#copy-draft").addEventListener("click", async (event) => {
  await navigator.clipboard.writeText(document.querySelector("#draft-text").textContent);
  event.currentTarget.textContent = "Copied";
  window.setTimeout(() => { event.currentTarget.textContent = "Copy text"; }, 1400);
});

function basePayload() {
  return {
    scenario_id: document.querySelector("#scenario-select").value,
    requester_id: document.querySelector("#manager-id").value.trim(),
    user_id: document.querySelector("#user-id").value.trim(),
    as_of: document.querySelector("#as-of").value,
  };
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "The request could not be completed.");
  return body;
}

function renderReview(report) {
  const employee = report.employee;
  document.querySelector("#employee-name").textContent = employee.display_name;
  document.querySelector("#employee-meta").textContent =
    `${employee.job_title} · ${employee.department} · ${employee.office_location}`;
  document.querySelector("#metric-total").textContent = report.summary.total;
  document.querySelector("#metric-expected").textContent = report.summary.expected;
  document.querySelector("#metric-review").textContent = report.summary.review;
  document.querySelector("#metric-suggestions").textContent = report.summary.suggestions;
  document.querySelector("#decision-boundary").textContent = report.decision_boundary;
  renderAccount(report.account_status);
  renderAccess(report.categories);
  renderSuggestions(report.access_suggestions);
  renderChangeOptions(report.categories, report.access_suggestions);
}

function renderAccount(account) {
  document.querySelector("#expiry-request").hidden = !account.service_desk_notice_draft;
  document.querySelector("#expiry-draft").textContent = account.service_desk_notice_draft || "";
  document.querySelector("#account-expiry").textContent = account.ad_account_expires_at || "Not configured";
  document.querySelector("#days-remaining").textContent = account.days_remaining ?? "—";
  document.querySelector("#contract-end").textContent = account.contract_end_date || "Not available";
  const status = document.querySelector("#account-status");
  status.textContent = account.status.replaceAll("_", " ");
  status.className = `tag ${statusClass(account.status)}`;
  const messages = document.querySelector("#account-messages");
  messages.replaceChildren(...account.messages.map((text) => element("li", {}, text)));
}

function renderAccess(categories) {
  const definitions = [
    ["Requires review", categories.review, "Review the evidence before requesting any change."],
    ["Role-aligned", categories.expected, "Access that matches the current documented rules."],
    ["Organization-wide", categories.organization_wide, "Common access reported separately to reduce noise."],
  ];
  const container = document.querySelector("#access-groups");
  container.replaceChildren(...definitions.map(([title, items, description]) => {
    const group = element("article", { className: "access-group" });
    const heading = element("div", { className: "access-group-heading" });
    const headingText = element("div");
    headingText.append(element("h3", {}, title), element("small", {}, description));
    heading.append(headingText, element("span", { className: "count-badge" }, String(items.length)));
    const list = element("div", { className: "access-list" });
    items.forEach((item) => list.append(accessRow(item)));
    group.append(heading, list);
    return group;
  }));
}

function accessRow(item) {
  const row = element("div", { className: "access-item" });
  const identity = element("div");
  identity.append(element("div", { className: "access-name" }, item.name), element("small", {}, item.resource_type.replaceAll("_", " ")));
  row.append(
    identity,
    element("small", {}, item.source),
    element("span", { className: "assignment" }, item.assignment),
    element("span", { className: "finding" }, item.evidence ? item.evidence.join(" · ") : item.purpose || "Purpose not documented"),
  );
  return row;
}

function renderSuggestions(suggestions) {
  const container = document.querySelector("#suggestions");
  if (!suggestions.length) {
    container.replaceChildren(element("p", { className: "empty-state" }, "No suggestions from the current approved profiles."));
    return;
  }
  container.replaceChildren(...suggestions.map((item) => {
    const card = element("article", { className: "suggestion-card" });
    const attributes = element("div", { className: "attribute-list" });
    item.matched_attributes.forEach((attribute) => attributes.append(element("span", { className: "attribute-chip" }, attribute)));
    card.append(element("h3", {}, item.name), element("p", {}, item.purpose), attributes);
    return card;
  }));
}

function renderChangeOptions(categories, suggestions) {
  const currentItems = [...categories.review, ...categories.expected, ...categories.organization_wide];
  renderOptions("#addition-options", suggestions.map((item) => item.name), "addition");
  renderOptions("#removal-options", currentItems.map((item) => item.name), "removal");
}

function renderOptions(selector, values, name) {
  const container = document.querySelector(selector);
  if (!values.length) {
    container.replaceChildren(element("p", { className: "empty-state" }, "No options available."));
    return;
  }
  container.replaceChildren(...values.map((value) => {
    const input = element("input", { type: "checkbox", name, value });
    const label = element("label");
    label.append(input, document.createTextNode(value));
    return label;
  }));
}

function selectedValues(name) {
  return [...document.querySelectorAll(`input[name='${name}']:checked`)].map((input) => input.value);
}

function statusClass(status) {
  if (status === "expired") return "danger";
  if (status === "expiring_soon") return "warning";
  if (status === "active") return "good";
  return "";
}

function element(tagName, properties = {}, text = null) {
  const node = document.createElement(tagName);
  Object.assign(node, properties);
  if (text !== null) node.textContent = text;
  return node;
}

function showMessage(text) {
  message.textContent = text;
  message.hidden = false;
  message.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideMessage() {
  message.hidden = true;
  message.textContent = "";
}



document.querySelector("#summary-button").addEventListener("click", async () => {
  if (!currentReview || !reviewPayload) return;
  const generation = reviewGeneration;
  const button = document.querySelector("#summary-button");
  const target = document.querySelector("#summary-result");
  button.disabled = true;
  target.hidden = false;
  target.textContent = "Preparing briefing…";
  try {
    const briefing = await postJson("/api/summary", reviewPayload);
    if (generation !== reviewGeneration) return;
    const modes = {deterministic: "Rule-based briefing", model_ordered: "AI-ordered evidence", fallback: "Rule-based fallback — AI unavailable or response rejected"};
    const list = element("ul", {className: "evidence-list"});
    briefing.evidence.forEach((item) => {
      const row = element("li");
      row.append(element("p", {}, item.text), element("small", {}, `${item.id} · ${item.source} · Report: ${item.report_path}`));
      list.append(row);
    });
    target.replaceChildren(
      element("h4", {}, modes[briefing.mode]),
      element("p", {}, briefing.overview), list,
      element("p", {className: "muted"}, briefing.coverage_notice),
      element("small", {}, `${briefing.metrics.duration_ms} ms · ${briefing.metrics.model_calls} model calls · ${briefing.metrics.evidence_count} evidence items`),
    );
  } catch (error) {
    if (generation === reviewGeneration) target.textContent = error.message;
  } finally {
    if (generation === reviewGeneration) button.disabled = false;
  }
});


const scenarioSelect = document.querySelector("#scenario-select");
let demoScenarios = [];
fetch("/api/demo-scenarios").then(async (response) => {
  if (!response.ok) throw new Error("Case list unavailable; you can still enter the demo identities.");
  const data = await response.json();
  demoScenarios = data.scenarios;
  demoScenarios.forEach((scenario) => scenarioSelect.append(element("option", {value: scenario.id}, scenario.title)));
  document.querySelector("#scenario-status").textContent = `${demoScenarios.length} Ankkalinnan esimerkkitapausta`;
}).catch((error) => { document.querySelector("#scenario-status").textContent = error.message; });

scenarioSelect.addEventListener("change", () => {
  const scenario = demoScenarios.find((item) => item.id === scenarioSelect.value);
  document.querySelector("#scenario-status").textContent = scenario ? scenario.title : "Nykyisen snapshotin tarkistus";
  document.querySelector("#manager-id").value = scenario ? scenario.manager : "roope.ankka";
  document.querySelector("#user-id").value = scenario ? scenario.employee : "aku.ankka";
  document.querySelector("#as-of").value = scenario ? scenario.review_date : "2026-10-07";
  document.querySelector("#reason").value = "";
  reviewForm.requestSubmit();
});
