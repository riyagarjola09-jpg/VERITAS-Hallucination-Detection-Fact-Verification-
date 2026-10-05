const input = document.getElementById('response-input');
const verifyBtn = document.getElementById('verify-btn');
const sampleBtn = document.getElementById('sample-btn');
const statusText = document.getElementById('status-text');
const ledger = document.getElementById('ledger');
const emptyState = document.getElementById('empty-state');
const trustMeter = document.getElementById('trust-meter');
const trustBarFill = document.getElementById('trust-bar-fill');
const trustValue = document.getElementById('trust-value');

const ORIGINAL_SAMPLE = input.value;

sampleBtn.addEventListener('click', () => {
  input.value = ORIGINAL_SAMPLE;
});

verifyBtn.addEventListener('click', runVerification);

async function runVerification() {
  const text = input.value.trim();
  if (!text) {
    statusText.textContent = 'Paste some text first.';
    return;
  }

  verifyBtn.disabled = true;
  statusText.textContent = 'Extracting claims, retrieving evidence, verifying…';
  ledger.innerHTML = '';
  emptyState.hidden = true;

  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    if (!res.ok) {
      statusText.textContent = data.error || 'Something went wrong.';
      emptyState.hidden = false;
      return;
    }

    renderReport(data);
    statusText.textContent = `${data.claim_count} claim(s) checked.`;
  } catch (err) {
    statusText.textContent = 'Could not reach the verification server.';
    emptyState.hidden = false;
  } finally {
    verifyBtn.disabled = false;
  }
}

function renderReport(report) {
  if (!report.claims.length) {
    emptyState.hidden = false;
    emptyState.textContent = 'No checkable factual claims were found in this text.';
    trustMeter.hidden = true;
    return;
  }

  trustMeter.hidden = false;
  const pct = Math.round(report.overall_trust_score * 100);
  trustBarFill.style.width = pct + '%';
  trustValue.textContent = pct + '%';

  ledger.innerHTML = '';
  report.claims.forEach((claim) => {
    ledger.appendChild(renderClaimRow(claim));
  });
}

function renderClaimRow(claim) {
  const row = document.createElement('div');
  row.className = 'claim-row';

  const mark = document.createElement('div');
  mark.className = `verdict-mark ${claim.verdict}`;
  row.appendChild(mark);

  const main = document.createElement('div');
  main.className = 'claim-main';

  const topRow = document.createElement('div');
  topRow.className = 'claim-top-row';
  topRow.innerHTML = `
    <span class="verdict-tag ${claim.verdict}">${claim.verdict}</span>
    <span class="claim-type">${claim.type}</span>
  `;
  main.appendChild(topRow);

  const text = document.createElement('div');
  text.className = 'claim-text';
  text.textContent = claim.text;
  main.appendChild(text);

  const confRow = document.createElement('div');
  confRow.className = 'confidence-row';
  const pct = Math.round(claim.confidence * 100);
  confRow.innerHTML = `
    <div class="confidence-bar">
      <div class="confidence-fill ${claim.verdict}" style="width:${pct}%"></div>
    </div>
    <span class="confidence-label">confidence ${pct}%</span>
  `;
  main.appendChild(confRow);

  if (claim.explanation) {
    const explanation = document.createElement('div');
    explanation.className = 'claim-explanation';
    explanation.textContent = claim.explanation;
    main.appendChild(explanation);
  }

  row.appendChild(main);
  return row;
}
