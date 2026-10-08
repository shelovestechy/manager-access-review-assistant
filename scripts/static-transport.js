// This is deliberately a public, synthetic presentation. It is not authorization.
window.staticDemoPost = async function(url, payload) {
  const record = window.staticDemoData.records[payload.scenario_id || ''];
  if (!record) throw new Error('Unknown demo scenario');
  if (payload.user_id !== record.employee || payload.requester_id.toLowerCase() !== record.manager.toLowerCase()) {
    throw new Error('This prepared example uses the selected sample identities. Choose another scenario to review another employee.');
  }
  if (payload.as_of !== record.review_date) throw new Error('This prepared example uses the displayed review date.');
  if (record.error) throw new Error(record.error);
  if (url === '/api/review') return structuredClone(record.report);
  if (url === '/api/summary') return structuredClone(record.briefing);
  if (url !== '/api/service-desk-draft') throw new Error('Unsupported demo action');
  const report = record.report;
  const additions = payload.additions || [];
  const removals = payload.removals || [];
  const knownAdditions = new Set(report.access_suggestions.map(item=>item.name));
  const knownRemovals = new Set(Object.values(report.categories).flat().map(item=>item.name));
  if (!additions.length && !removals.length) throw new Error('Select at least one change.');
  if (additions.some(x=>!knownAdditions.has(x)) || removals.some(x=>!knownRemovals.has(x))) throw new Error('Select changes from this example only.');
  if (!payload.reason || !payload.reason.trim()) throw new Error('Provide a business reason.');
  const e = report.employee;
  const lines = [`Subject: Access change request - ${e.display_name}`, '', 'Hello Service Desk,', '',
    `Please review the following access changes for ${e.display_name} (${e.user_id}).`,
    `Role: ${e.job_title}`, `Department: ${e.department}`, `Location: ${e.office_location}`, ''];
  if (additions.length) lines.push('Requested additions:', ...additions.map(x=>`- ${x}`), '');
  if (removals.length) lines.push('Requested removals:', ...removals.map(x=>`- ${x}`), '');
  lines.push(`Business reason: ${payload.reason.trim()}`, `Requesting manager: ${record.manager}`, '',
    'Please validate eligibility and implement only through the normal approval process.',
    'The assistant created this draft but did not make any access changes.');
  return {draft:lines.join('\n'),submitted:false};
};
