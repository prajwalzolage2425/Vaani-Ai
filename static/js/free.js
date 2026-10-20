/**
 * Free Mode Controller for VaaniAI
 * 3-Pass Pipeline: Record → Transcribe → Identify → Analyze → Report
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const btnRecord = document.getElementById("free-btn-record");
  const recordLabel = document.getElementById("free-record-label");
  const recTimer = document.getElementById("free-rec-timer");
  const audioPreview = document.getElementById("free-audio-preview");
  const previewPlayer = document.getElementById("free-preview-player");
  const btnSubmit = document.getElementById("free-btn-submit");
  const btnIdentify = document.getElementById("free-btn-identify");
  const btnAnalyze = document.getElementById("free-btn-analyze");
  const btnRestart = document.getElementById("free-btn-restart");
  const micError = document.getElementById("free-mic-error");
  const loadingOverlay = document.getElementById("free-loading");
  const loadingStep = document.getElementById("free-loading-step");

  // Step panels
  const panelRecord = document.getElementById("panel-record");
  const panelTranscribe = document.getElementById("panel-transcribe");
  const panelIdentify = document.getElementById("panel-identify");
  const panelReport = document.getElementById("panel-report");

  // Step indicators
  const stepInds = [1, 2, 3, 4, 5].map(n => document.getElementById(`step-ind-${n}`));
  const stepLines = ["line-1-2", "line-2-3", "line-3-4", "line-4-5"].map(id => document.getElementById(id));

  // State
  let isRecording = false;
  let audioBlob = null;
  let currentAudioUrl = null;
  let audioToken = "";  // server-side reference to saved audio
  let heardText = "";
  let heardTransliteration = "";
  let intendedText = "";

  // Sthana diagram
  if (typeof SthanaDiagram !== "undefined") {
    SthanaDiagram.init("free-sthana-diagram");
  }

  // ── Step Navigation ──────────────────────────────────────
  function activateStep(stepNum) {
    stepInds.forEach((el, i) => {
      if (!el) return;
      el.classList.remove("active", "done");
      if (i + 1 < stepNum) el.classList.add("done");
      else if (i + 1 === stepNum) el.classList.add("active");
    });
    stepLines.forEach((el, i) => {
      if (!el) return;
      el.classList.toggle("done", i + 1 < stepNum);
    });
  }

  function showPanel(panel) {
    [panelRecord, panelTranscribe, panelIdentify, panelReport].forEach(p => {
      if (p) p.style.display = "none";
    });
    if (panel) {
      panel.style.display = "block";
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function showLoading(msg) {
    if (loadingStep) loadingStep.textContent = msg;
    if (loadingOverlay) loadingOverlay.classList.add("active");
  }

  function hideLoading() {
    if (loadingOverlay) loadingOverlay.classList.remove("active");
  }

  function showError(msg) {
    if (micError) {
      micError.textContent = msg;
      micError.style.display = "block";
    }
  }

  // ── STEP 1: Recording ────────────────────────────────────
  if (btnRecord) {
    btnRecord.addEventListener("click", async () => {
      if (!isRecording) {
        if (micError) micError.style.display = "none";
        const started = await AudioService.startRecording(
          (timeStr) => { if (recTimer) recTimer.textContent = `${timeStr}s`; },
          (errorMsg) => { showError(errorMsg); }
        );
        if (started) {
          isRecording = true;
          btnRecord.classList.add("recording");
          if (recordLabel) recordLabel.textContent = "Stop";
          if (audioPreview) audioPreview.style.display = "none";
          if (btnSubmit) btnSubmit.style.display = "none";
        }
      } else {
        btnRecord.classList.remove("recording");
        if (recordLabel) recordLabel.textContent = "Record";
        isRecording = false;

        audioBlob = await AudioService.stopRecording();
        if (audioBlob && audioBlob.size > 0) {
          if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);
          currentAudioUrl = URL.createObjectURL(audioBlob);
          if (previewPlayer) { previewPlayer.src = currentAudioUrl; previewPlayer.load(); }
          if (audioPreview) audioPreview.style.display = "block";
          if (btnSubmit) btnSubmit.style.display = "inline-flex";
        } else {
          showError("Recording was empty. Please speak clearly and try again.");
        }
      }
    });
  }

  // ── STEP 1→2: Submit audio for transcription (Pass 1) ───
  if (btnSubmit) {
    btnSubmit.addEventListener("click", async () => {
      if (!audioBlob) return showError("No recording found. Please record first.");

      showLoading("Uploading audio to Gemini...");
      setTimeout(() => { if (loadingStep) loadingStep.textContent = "Transcribing phonemes (Pass 1)..."; }, 800);

      try {
        const formData = new FormData();
        formData.append("audio", audioBlob, "free_speech.webm");

        const res = await fetch("/api/free/transcribe", { method: "POST", body: formData });
        const data = await res.json();

        if (!data.success) throw new Error(data.error || "Transcription failed");

        heardText = data.heard_text || "";
        heardTransliteration = data.heard_transliteration || "";
        audioToken = data.audio_token || "";

        if (!heardText) throw new Error("Could not detect any speech. Please speak louder and try again.");

        // Show Pass 1 result
        const heardEl = document.getElementById("free-heard-text");
        const translitEl = document.getElementById("free-heard-translit");
        const clarityBar = document.getElementById("free-clarity-bar");
        const clarityVal = document.getElementById("free-clarity-val");

        if (heardEl) heardEl.textContent = heardText;
        if (translitEl) translitEl.textContent = heardTransliteration;
        if (clarityBar) clarityBar.style.width = `${data.clarity || 0}%`;
        if (clarityVal) clarityVal.textContent = `${data.clarity || 0}%`;

        activateStep(2);
        showPanel(panelTranscribe);

      } catch (err) {
        showError(`Transcription failed: ${err.message}`);
      } finally {
        hideLoading();
      }
    });
  }

  // ── STEP 2→3: Identify shloka (Pass 2) ──────────────────
  if (btnIdentify) {
    btnIdentify.addEventListener("click", async () => {
      if (!heardText) return;

      showLoading("Identifying shloka source...");
      setTimeout(() => { if (loadingStep) loadingStep.textContent = "Consulting Vedic corpus & IKS knowledge base..."; }, 1000);

      try {
        const res = await fetch("/api/free/identify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ heard_text: heardText, audio_token: audioToken })
        });
        const data = await res.json();

        if (!data.success) throw new Error(data.error || "Identification failed");

        // Populate UI
        const sourceEl = document.getElementById("free-source-text");
        const meaningEl = document.getElementById("free-meaning-text");
        const intendedInput = document.getElementById("free-intended-input");

        if (sourceEl) sourceEl.textContent = data.source || "Source not identified";
        if (meaningEl) meaningEl.textContent = data.meaning || "Meaning not available";
        if (intendedInput) intendedInput.value = data.standard_text || heardText;

        // IKS Analysis
        const iksPanel = document.getElementById("free-iks-panel");
        const iksDetails = document.getElementById("free-iks-details");
        const iks = data.iks_analysis || {};

        if (iksPanel && iksDetails && Object.keys(iks).length > 0) {
          let iksHtml = "";
          if (iks.vedanga_context) iksHtml += `<div style="display: flex; align-items: flex-start; gap: 0.4rem; margin-bottom: 0.4rem;">${Icons.book("ui-icon ui-icon-sm")} <div><strong>Vedāṅga Context:</strong> ${iks.vedanga_context}</div></div>`;
          if (iks.chandas) iksHtml += `<div style="display: flex; align-items: flex-start; gap: 0.4rem; margin-bottom: 0.4rem;">${Icons.ruler("ui-icon ui-icon-sm")} <div><strong>Chandas (Meter):</strong> ${iks.chandas}</div></div>`;
          if (iks.key_phonetic_features) iksHtml += `<div style="display: flex; align-items: flex-start; gap: 0.4rem; margin-bottom: 0.4rem;">${Icons.target("ui-icon ui-icon-sm")} <div><strong>Key Phonetic Features:</strong> ${iks.key_phonetic_features}</div></div>`;
          if (iks.spiritual_significance) iksHtml += `<div style="display: flex; align-items: flex-start; gap: 0.4rem;">${Icons.lotus("ui-icon ui-icon-sm")} <div><strong>Spiritual Significance:</strong> ${iks.spiritual_significance}</div></div>`;

          if (iksHtml) {
            iksDetails.innerHTML = iksHtml;
            iksPanel.style.display = "block";
          }
        }

        activateStep(3);
        showPanel(panelIdentify);

      } catch (err) {
        showError(`Identification failed: ${err.message}`);
        // Still show identify panel with heard text as editable
        const intendedInput = document.getElementById("free-intended-input");
        if (intendedInput) intendedInput.value = heardText;
        activateStep(3);
        showPanel(panelIdentify);
      } finally {
        hideLoading();
      }
    });
  }

  // ── STEP 3→4→5: Full Shiksha analysis (Pass 3) ─────────
  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", async () => {
      const intendedInput = document.getElementById("free-intended-input");
      intendedText = intendedInput ? intendedInput.value.trim() : heardText;

      if (!intendedText) return showError("Please provide the intended text.");

      showLoading("Running character-level diff (Pass 3)...");
      setTimeout(() => { if (loadingStep) loadingStep.textContent = "Gemini audio re-check for subtle errors..."; }, 1200);
      setTimeout(() => { if (loadingStep) loadingStep.textContent = "Applying Pāṇinīya Śikṣā rules (Sthāna & Prayatna)..."; }, 2500);

      try {
        const res = await fetch("/api/free/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            heard_text: heardText,
            intended_text: intendedText,
            audio_token: audioToken
          })
        });
        const data = await res.json();

        if (!data.success) throw new Error(data.error || "Analysis failed");

        renderReport(data);
        activateStep(5);
        showPanel(panelReport);

      } catch (err) {
        showError(`Analysis failed: ${err.message}`);
      } finally {
        hideLoading();
      }
    });
  }

  // ── Render Full Report ───────────────────────────────────
  function renderReport(data) {
    // Score
    const scoreNum = document.getElementById("free-score-num");
    const scoreCircle = document.getElementById("free-score-circle");
    const score = data.score || 0;
    if (scoreNum) scoreNum.textContent = score;
    if (scoreCircle) {
      scoreCircle.className = "score-badge-circle " +
        (score >= 85 ? "score-perfect" : score >= 60 ? "score-mid" : "score-low");
    }

    // Stats
    const statTotal = document.getElementById("free-stat-total");
    const statMatched = document.getElementById("free-stat-matched");
    const statErrors = document.getElementById("free-stat-errors");
    if (statTotal) statTotal.textContent = data.total_phonemes || 0;
    if (statMatched) statMatched.textContent = data.matched_phonemes || 0;
    if (statErrors) statErrors.textContent = data.error_count || 0;

    // Heard vs Intended
    const rptHeard = document.getElementById("free-rpt-heard");
    const rptIntended = document.getElementById("free-rpt-intended");
    if (rptHeard) rptHeard.textContent = data.heard_text || heardText;
    if (rptIntended) rptIntended.textContent = data.intended_text || intendedText;

    // Character Breakdown
    const charContainer = document.getElementById("free-char-breakdown");
    if (charContainer) {
      charContainer.innerHTML = "";
      (data.char_results || []).forEach(cr => {
        const box = document.createElement("div");
        box.className = `char-box deva-text ${cr.status === "correct" ? "char-correct" : cr.status === "error" ? "char-error" : ""}`;
        box.textContent = cr.char;
        if (cr.status === "error") {
          box.title = `Heard '${cr.heard}' instead of '${cr.char}'`;
        }
        box.style.cursor = "pointer";
        box.addEventListener("click", () => {
          const meta = cr.feedback?.expected_meta;
          if (meta && meta.sthana && typeof SthanaDiagram !== "undefined") {
            SthanaDiagram.highlight(meta.sthana, meta.sthana_name);
            // Update banner
            const nameEl = document.getElementById("free-sthana-name");
            const sutraEl = document.getElementById("free-sthana-sutra");
            if (nameEl) nameEl.textContent = meta.sthana_name || meta.sthana;
            if (sutraEl) sutraEl.textContent = meta.sutra || "";
          }
        });
        charContainer.appendChild(box);
      });
    }

    // Tip
    const tipEl = document.getElementById("free-tip-content");
    if (tipEl) tipEl.textContent = data.tip || "";

    // Error Details
    const errorList = document.getElementById("free-error-list");
    if (errorList) {
      errorList.innerHTML = "";
      const errors = data.errors || [];
      if (errors.length === 0) {
        errorList.innerHTML = `
          <div class="sutra-banner" style="background: var(--iks-correct-bg); border-left-color: var(--iks-correct);">
            <div class="sutra-title" style="color: var(--iks-correct);">शुद्धोऽयं पाठः (Perfect Recitation)</div>
            <div class="sutra-text" style="color: #145A32;">All sounds matched the canonical text with proper Sthāna and Prayatna. उत्कृष्टम्!</div>
          </div>
        `;
      } else {
        errors.forEach((err, idx) => {
          const div = document.createElement("div");
          div.className = "error-item";
          div.style.cursor = "pointer";
          div.innerHTML = `
            <div class="error-title">
              <span class="deva-text" style="display: inline-flex; align-items: center; gap: 0.35rem;">
                <span>दोष ${idx + 1}:</span> <strong>${err.expected_char || "?"}</strong> ${Icons.arrowRight("ui-icon ui-icon-sm")} <strong>${err.heard_char || "?"}</strong>
              </span>
              <span class="badge-demo" style="background: var(--status-error-bg); color: var(--status-error); border-color: var(--status-error-border);">
                ${err.difference_summary || "Phonetic Deviation"}
              </span>
            </div>
            <div class="error-sub">${err.corrective_tip || ""}</div>
            ${err.expected_sutra ? `
              <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--accent-gold-dark); font-weight: 700; display: flex; align-items: center; gap: 0.35rem;">
                ${Icons.book("ui-icon ui-icon-sm")} <span>पाणिनिसूत्रम्:</span> <span class="deva-text" style="color: var(--text-primary);">${err.expected_sutra}</span>
              </div>
            ` : ""}
          `;
          div.addEventListener("click", () => {
            if (err.expected_sthana && err.heard_sthana && typeof SthanaDiagram !== "undefined") {
              SthanaDiagram.compare(err.expected_sthana, err.heard_sthana);
            }
          });
          errorList.appendChild(div);
        });

        // Show first error on diagram
        const first = errors[0];
        if (first && first.expected_sthana && first.heard_sthana && typeof SthanaDiagram !== "undefined") {
          SthanaDiagram.compare(first.expected_sthana, first.heard_sthana);
        }
      }
    }
  }

  // ── Restart ──────────────────────────────────────────────
  if (btnRestart) {
    btnRestart.addEventListener("click", () => {
      // Reset state
      isRecording = false;
      audioBlob = null;
      audioToken = "";
      heardText = "";
      intendedText = "";
      if (currentAudioUrl) { URL.revokeObjectURL(currentAudioUrl); currentAudioUrl = null; }

      // Reset UI
      if (btnRecord) btnRecord.classList.remove("recording");
      if (recordLabel) recordLabel.textContent = "Record";
      if (recTimer) recTimer.textContent = "0.0s";
      if (audioPreview) audioPreview.style.display = "none";
      if (previewPlayer) previewPlayer.src = "";
      if (btnSubmit) btnSubmit.style.display = "none";
      if (micError) micError.style.display = "none";

      activateStep(1);
      showPanel(panelRecord);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Initial state
  activateStep(1);
  showPanel(panelRecord);
});
