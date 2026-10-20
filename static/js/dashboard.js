/**
 * Dashboard Controller for VaaniAI
 * Visualizes user progress, Chart.js score history, weak sounds grouped by varga,
 * and comprehensive Session History Log with error diagnostic reports and deletion.
 */

document.addEventListener("DOMContentLoaded", async () => {
  const userId = "student_demo";
  const statAttempts = document.getElementById("stat-attempts");
  const statAvgScore = document.getElementById("stat-avg-score");
  const statWeakVarga = document.getElementById("stat-weak-varga");
  const weakSoundsContainer = document.getElementById("weak-sounds-container");
  const attemptsTableBody = document.getElementById("attempts-table-body");
  const historyCountBadge = document.getElementById("history-count-badge");
  const chartCanvas = document.getElementById("progressChart");
  const btnClearHistory = document.getElementById("btn-clear-history");

  // Report Modal elements
  const reportModal = document.getElementById("history-report-modal");
  const modalBtnClose = document.getElementById("modal-btn-close");
  const modalBtnDone = document.getElementById("modal-btn-done");
  const modalBtnDeleteThis = document.getElementById("modal-btn-delete-this");
  const modalAttemptMeta = document.getElementById("modal-attempt-meta");
  const modalScoreNum = document.getElementById("modal-score-num");
  const modalScoreCircle = document.getElementById("modal-score-circle");
  const modalScoreStatus = document.getElementById("modal-score-status");
  const modalErrorBadgeWrap = document.getElementById("modal-error-badge-wrap");
  const modalTargetText = document.getElementById("modal-target-text");
  const modalHeardText = document.getElementById("modal-heard-text");
  const modalCharSection = document.getElementById("modal-char-section");
  const modalCharContainer = document.getElementById("modal-char-container");
  const modalErrorList = document.getElementById("modal-error-list");
  const modalTipContent = document.getElementById("modal-tip-content");

  // Confirmation Modal elements
  const confirmModal = document.getElementById("history-confirm-modal");
  const confirmBtnClose = document.getElementById("confirm-btn-close");
  const confirmBtnCancel = document.getElementById("confirm-btn-cancel");
  const confirmBtnOk = document.getElementById("confirm-btn-ok");
  const confirmModalTitle = document.getElementById("confirm-modal-title");
  const confirmModalMsg = document.getElementById("confirm-modal-msg");

  let progressChart = null;
  let currentAttempts = [];
  let pendingConfirmAction = null;
  let activeModalAttempt = null;

  // Initial load
  await loadDashboardData();

  async function loadDashboardData() {
    try {
      const data = await API.getProgress(userId);
      const progress = data.progress || { attempts: [], weak_sounds: {} };
      currentAttempts = progress.attempts || [];
      renderStats(progress);
      renderChart(currentAttempts);
      renderWeakSounds(progress.weak_sounds || {});
      renderAttemptsTable(currentAttempts);
    } catch (err) {
      console.error("Dashboard progress loading failed:", err);
    }
  }

  function renderStats(progress) {
    const attempts = progress.attempts || [];
    const total = attempts.length;
    statAttempts.textContent = total;

    if (total === 0) {
      statAvgScore.textContent = "--";
      statWeakVarga.textContent = "None yet";
      return;
    }

    const sumScore = attempts.reduce((acc, a) => acc + (a.score || 0), 0);
    const avg = Math.round(sumScore / total);
    statAvgScore.textContent = `${avg}%`;

    // Find varga with highest errors
    let maxVarga = "None";
    let maxErrors = 0;
    const weakSounds = progress.weak_sounds || {};
    for (const [varga, info] of Object.entries(weakSounds)) {
      if (info.error_count > maxErrors) {
        maxErrors = info.error_count;
        maxVarga = varga;
      }
    }
    statWeakVarga.textContent = maxErrors > 0 ? `${maxVarga} (${maxErrors} err)` : "None (All Clean)";
  }

  function renderChart(attempts) {
    if (!chartCanvas) return;

    const labels = attempts.length > 0 
      ? attempts.map((_, i) => `Attempt ${i + 1}`) 
      : ["Attempt 1", "Attempt 2", "Attempt 3", "Attempt 4", "Attempt 5"];
    
    const scores = attempts.length > 0
      ? attempts.map(a => a.score)
      : [72, 78, 85, 88, 94];

    if (progressChart) {
      progressChart.destroy();
    }

    const ctx = chartCanvas.getContext("2d");
    progressChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Pāṇinian Pronunciation Score",
          data: scores,
          borderColor: "#E65100",
          backgroundColor: "rgba(230, 81, 0, 0.08)",
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointBackgroundColor: "#E65100",
          pointBorderColor: "#FFFFFF",
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 0,
            max: 100,
            grid: {
              color: "#E2E8F0",
              drawBorder: false
            },
            ticks: {
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: "600", size: 12 },
              color: "#64748B",
              callback: val => `${val}%`
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
              color: "#64748B"
            }
          }
        },
        plugins: {
          legend: {
            labels: {
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: "700" },
              color: "#0F172A",
              boxWidth: 14,
              boxHeight: 14,
              borderRadius: 3
            }
          },
          tooltip: {
            backgroundColor: "#0F172A",
            titleFont: { family: "'Plus Jakarta Sans', sans-serif" },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif", weight: "600" },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: ctx => `Śikṣā Score: ${ctx.parsed.y} / 100`
            }
          }
        }
      }
    });
  }

  function renderWeakSounds(weakSounds) {
    weakSoundsContainer.innerHTML = "";
    const vargas = Object.keys(weakSounds);

    if (vargas.length === 0) {
      weakSoundsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--brown-muted); background: var(--cream-sand); border-radius: var(--radius-sm);">
          No persistent phonetic errors identified yet! Continue your practice sessions to build personalized analytics.
        </div>
      `;
      return;
    }

    const vargaLabels = {
      "ka-varga": "क-वर्ग (Ka-Varga / Kaṇṭhya)",
      "cha-varga": "च-वर्ग (Ca-Varga / Tālavya)",
      "ta-varga-murdhanya": "ट-वर्ग (Ṭa-Varga / Mūrdhanya)",
      "ta-varga-dantya": "त-वर्ग (Ta-Varga / Dantya)",
      "pa-varga": "प-वर्ग (Pa-Varga / Oṣṭhya)",
      "antastha": "अन्तःस्थ (Antastha - Semivowels)",
      "ushma": "ऊष्म (Ūṣma - Sibilants & Aspirate)",
      "svara": "स्वर (Svara - Vowels)"
    };

    vargas.forEach(vargaKey => {
      const vargaInfo = weakSounds[vargaKey];
      const card = document.createElement("div");
      card.className = "varga-card";

      let soundChipsHtml = "";
      for (const [sym, soundObj] of Object.entries(vargaInfo.sounds || {})) {
        soundChipsHtml += `
          <div class="sound-chip" title="${soundObj.tip || ''}">
            <span class="sound-chip-sym deva-text">${sym}</span>
            <span style="font-size: 0.85rem; color: var(--brown-muted);">${soundObj.roman || ''}</span>
            <span class="sound-chip-count">${soundObj.count} err</span>
          </div>
        `;
      }

      card.innerHTML = `
        <div class="varga-title">
          <span>${vargaLabels[vargaKey] || vargaKey}</span>
          <span style="font-size: 0.85rem; color: var(--iks-error); font-weight: 700;">${vargaInfo.error_count} total</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
          ${soundChipsHtml}
        </div>
      `;
      weakSoundsContainer.appendChild(card);
    });
  }

  function renderAttemptsTable(attempts) {
    if (historyCountBadge) {
      historyCountBadge.textContent = `${attempts.length} Record${attempts.length === 1 ? '' : 's'}`;
    }

    attemptsTableBody.innerHTML = "";
    if (attempts.length === 0) {
      attemptsTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
            <div style="margin-bottom: 0.5rem; color: var(--text-muted);">${Icons.scroll("ui-icon ui-icon-lg")}</div>
            <div style="font-weight: 600; color: var(--text-primary); font-size: 1.05rem;">No pronunciation history found</div>
            <p style="margin-top: 0.25rem; font-size: 0.9rem;">Record sounds or shlokas in Practice or Free Mode to start tracking your Pāṇinian learning curve.</p>
          </td>
        </tr>
      `;
      return;
    }

    // Show most recent first
    const reversed = [...attempts].reverse();
    reversed.forEach((att, idx) => {
      const tr = document.createElement("tr");
      tr.className = "attempt-row";
      tr.style.cursor = "pointer";
      
      const attemptNum = reversed.length - idx;
      let dateStr = "Recent";
      if (att.created_at) {
        try {
          const d = new Date(att.created_at);
          dateStr = d.toLocaleDateString([], { month: "short", day: "numeric" }) + ", " + 
                    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        } catch (e) {
          dateStr = "Recent";
        }
      }

      const score = att.score || 0;
      const scoreColor = score >= 85 ? "var(--status-clean)" : score >= 60 ? "var(--brand-primary)" : "var(--status-error)";
      const errorCount = (att.errors || []).length;
      
      // Target display
      const targetDisplay = att.target_text || att.item_id || "Practice Item";
      const subDisplay = att.target_transliteration ? `(${att.target_transliteration})` : (att.item_id !== "free_mode" ? att.item_id : "");
      
      // Heard display
      const heardDisplay = att.recognized_text || "—";

      tr.innerHTML = `
        <td data-label="#" style="font-weight: 700; color: var(--text-muted);">${attemptNum}</td>
        <td data-label="Time" style="font-size: 0.85rem; color: var(--text-muted); white-space: nowrap;">${dateStr}</td>
        <td data-label="Target">
          <div class="deva-text" style="font-weight: 600; font-size: 1.08rem; color: var(--text-primary);">${escapeHtml(targetDisplay)}</div>
          ${subDisplay ? `<div style="font-size: 0.78rem; color: var(--text-muted); font-style: italic; margin-top: 0.15rem;">${escapeHtml(subDisplay)}</div>` : ''}
        </td>
        <td data-label="Heard">
          <span class="deva-text" style="font-size: 1.02rem; color: var(--text-secondary); font-weight: 500;">${escapeHtml(heardDisplay)}</span>
        </td>
        <td data-label="Score" style="font-weight: 800; font-size: 1.15rem; color: ${scoreColor};">${score}%</td>
        <td data-label="Status">
          ${errorCount === 0 
            ? `<span class="badge-demo" style="background: var(--status-clean-bg); color: var(--status-clean); border-color: var(--status-clean-border);">शुद्ध (Clean)</span>`
            : `<span class="badge-demo" style="background: var(--status-error-bg); color: var(--status-error); border-color: var(--status-error-border);">${errorCount} दोष (${errorCount} Err)</span>`
          }
        </td>
        <td data-label="Actions" style="text-align: right; white-space: nowrap;">
          <button class="btn-action-view" data-index="${idx}" title="View detailed Shiksha error report">
            ${Icons.report("ui-icon ui-icon-sm")} <span>Report</span>
          </button>
          <button class="btn-action-delete" data-id="${att._id}" title="Delete this attempt record" style="margin-left: 0.4rem;">
            ${Icons.trash("ui-icon ui-icon-sm")}
          </button>
        </td>
      `;

      // Row click opens the report modal (except if clicking delete button)
      tr.addEventListener("click", (e) => {
        if (e.target.closest(".btn-action-delete")) {
          return; // Handled by delete button listener
        }
        openReportModal(att, attemptNum, dateStr);
      });

      // Delete button listener
      const btnDelete = tr.querySelector(".btn-action-delete");
      if (btnDelete) {
        btnDelete.addEventListener("click", (e) => {
          e.stopPropagation();
          promptDeleteSingle(att._id, attemptNum);
        });
      }

      attemptsTableBody.appendChild(tr);
    });
  }

  // ---------------------------------------------------------------------------
  // Diagnostic Report Modal ("Where You Got Wrong")
  // ---------------------------------------------------------------------------
  function openReportModal(att, attemptNum, dateStr) {
    activeModalAttempt = att;
    const score = att.score || 0;
    const errors = att.errors || [];
    const errorCount = errors.length;

    // 1. Meta
    modalAttemptMeta.textContent = `Attempt #${attemptNum} • Recorded on ${dateStr} • Target: ${att.target_title || att.item_id || 'Practice'}`;

    // 2. Score & Status
    modalScoreNum.textContent = score;
    modalScoreCircle.className = "score-badge-circle " + 
      (score >= 85 ? "score-perfect" : score >= 60 ? "score-mid" : "score-low");

    if (score >= 85) {
      modalScoreStatus.innerHTML = `<span style="color: var(--iks-correct);">उत्कृष्टम् / शुद्धम् (Accurate Pāṇinian Articulation)</span>`;
    } else if (score >= 60) {
      modalScoreStatus.innerHTML = `<span style="color: var(--saffron-primary);">मध्यमम् (Minor Phonetic Deviations)</span>`;
    } else {
      modalScoreStatus.innerHTML = `<span style="color: var(--iks-error);">दोषयुक्तम् (Substantial Deviations)</span>`;
    }

    if (errorCount === 0) {
      modalErrorBadgeWrap.innerHTML = `
        <span class="badge-demo" style="background: var(--status-clean-bg); color: var(--status-clean); border-color: var(--status-clean-border); display: inline-flex; align-items: center; gap: 0.35rem;">
          ${Icons.check("ui-icon ui-icon-sm")} 0 Articulatory Errors Detected
        </span>
      `;
    } else {
      modalErrorBadgeWrap.innerHTML = `
        <span class="badge-demo" style="background: var(--status-error-bg); color: var(--status-error); border-color: var(--status-error-border); display: inline-flex; align-items: center; gap: 0.35rem;">
          ${Icons.alert("ui-icon ui-icon-sm")} ${errorCount} Phonetic Deviation${errorCount === 1 ? '' : 's'} Identified
        </span>
      `;
    }

    // 3. Utterances comparison
    const targetFull = att.target_text || att.item_id || "—";
    const translit = att.target_transliteration ? ` (${att.target_transliteration})` : "";
    modalTargetText.textContent = `${targetFull}${translit}`;
    modalHeardText.textContent = att.recognized_text || "—";

    // 4. Character Breakdown Matrix (if available)
    const charResults = att.char_results || [];
    if (charResults && charResults.length > 0) {
      modalCharContainer.innerHTML = "";
      charResults.forEach(cr => {
        const box = document.createElement("div");
        box.className = `char-box deva-text ${cr.status === "correct" ? "char-correct" : cr.status === "error" ? "char-error" : ""}`;
        box.textContent = cr.char;
        if (cr.status === "error") {
          box.title = `Deviated: Expected '${cr.char}', detected '${cr.heard}'`;
        } else {
          box.title = `Clean: Correctly articulated '${cr.char}'`;
        }
        modalCharContainer.appendChild(box);
      });
      modalCharSection.style.display = "block";
    } else {
      modalCharSection.style.display = "none";
    }

    // 5. "Where You Got Wrong" - Detailed Shiksha Diagnostics
    modalErrorList.innerHTML = "";
    if (errorCount === 0) {
      modalErrorList.innerHTML = `
        <div class="sutra-banner" style="background: var(--status-clean-bg); border-left-color: var(--status-clean); padding: 1.25rem;">
          <div class="sutra-title" style="color: var(--status-clean); font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
            ${Icons.award("ui-icon ui-icon-md")} <span>शुद्धोऽयं वर्णः (Flawless Pāṇinian Articulation)</span>
          </div>
          <div class="sutra-text" style="color: #065F46; font-size: 0.95rem; margin-top: 0.35rem; line-height: 1.5;">
            No articulatory deviations found! Every phoneme aligned accurately with its prescribed 
            <em>Sthāna</em> (place of articulation) and <em>Prayatna</em> (articulatory effort) according to Pāṇinīya Śikṣā.
          </div>
        </div>
      `;
    } else {
      errors.forEach((err, idx) => {
        const card = document.createElement("div");
        card.className = "report-error-card";

        const expChar = err.expected_char || "—";
        const hrdChar = err.heard_char || "—";
        const diffSummary = err.difference_summary || "Phonetic Deviation";
        const expSthana = err.expected_sthana_name || err.expected_sthana || "";
        const hrdSthana = err.heard_sthana_name || err.heard_sthana || "";
        const sutra = err.expected_sutra || "";
        const tip = err.corrective_tip || "Ensure correct anatomical placement of tongue and breath control.";

        let sthanaHtml = "";
        if (expSthana || hrdSthana) {
          sthanaHtml = `
            <div class="sthana-comparison-row">
              <div>
                <span style="color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; font-weight: 700; margin-right: 0.3rem;">Expected Sthāna:</span>
                <span class="sthana-pill sthana-pill-expected">${Icons.target("ui-icon ui-icon-sm")} ${escapeHtml(expSthana || 'Canonical')}</span>
              </div>
              <div style="color: var(--text-muted); display: flex; align-items: center;">${Icons.arrowRight("ui-icon ui-icon-sm")}</div>
              <div>
                <span style="color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; font-weight: 700; margin-right: 0.3rem;">Articulated Sthāna:</span>
                <span class="sthana-pill sthana-pill-heard">${Icons.alert("ui-icon ui-icon-sm")} ${escapeHtml(hrdSthana || 'Shifted')}</span>
              </div>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="report-error-header">
            <div class="deva-text" style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
              <span>दोष ${idx + 1}:</span>
              <span style="color: var(--status-clean);">${escapeHtml(expChar)}</span>
              <span style="color: var(--text-muted);">${Icons.arrowRight("ui-icon ui-icon-sm")}</span>
              <span style="color: var(--status-error);">${escapeHtml(hrdChar)}</span>
            </div>
            <span class="badge-demo" style="background: var(--status-error-bg); color: var(--status-error); border-color: var(--status-error-border);">
              ${escapeHtml(diffSummary)}
            </span>
          </div>

          ${sthanaHtml}

          ${sutra ? `
            <div style="font-size: 0.88rem; color: var(--accent-gold-dark); font-weight: 700; margin: 0.4rem 0; display: flex; align-items: center; gap: 0.35rem;">
              ${Icons.book("ui-icon ui-icon-sm")}
              <span>पाणिनिसूत्रम्:</span> <span class="deva-text" style="color: var(--text-primary); font-size: 0.95rem;">${escapeHtml(sutra)}</span>
            </div>
          ` : ""}

          <div style="font-size: 0.92rem; color: var(--text-secondary); line-height: 1.5; margin-top: 0.45rem; display: flex; align-items: flex-start; gap: 0.4rem;">
            <span style="color: var(--accent-gold-dark); margin-top: 0.15rem;">${Icons.lightbulb("ui-icon ui-icon-sm")}</span>
            <div><strong>Pāṇinian Remedy:</strong> ${escapeHtml(tip)}</div>
          </div>
        `;
        modalErrorList.appendChild(card);
      });
    }

    // 6. Pedagogical guidance tip
    modalTipContent.textContent = att.tip || (errorCount === 0 
      ? "उत्कृष्टम्! Your vocal articulation conforms to classical Sanskrit phonetic rules." 
      : "Focus on the highlighted Sthāna place of contact. Practice minimal pairs slowly.");

    // Display modal
    reportModal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeReportModal() {
    reportModal.style.display = "none";
    document.body.style.overflow = "";
    activeModalAttempt = null;
  }

  if (modalBtnClose) modalBtnClose.addEventListener("click", closeReportModal);
  if (modalBtnDone) modalBtnDone.addEventListener("click", closeReportModal);

  // Close report on outside backdrop click
  if (reportModal) {
    reportModal.addEventListener("click", (e) => {
      if (e.target === reportModal) closeReportModal();
    });
  }

  // Delete from inside the report modal
  if (modalBtnDeleteThis) {
    modalBtnDeleteThis.addEventListener("click", () => {
      if (!activeModalAttempt) return;
      const attId = activeModalAttempt._id;
      closeReportModal();
      promptDeleteSingle(attId);
    });
  }

  // ---------------------------------------------------------------------------
  // Deletion Workflows (Single Attempt & Clear All)
  // ---------------------------------------------------------------------------
  function promptDeleteSingle(attemptId, attemptNum) {
    const numLabel = attemptNum ? `Attempt #${attemptNum}` : "this attempt";
    openConfirmModal(
      "Delete Attempt Record (विवरण निष्कासनम्)",
      `Are you sure you want to delete ${numLabel} from your session history? This will remove its score and phonetic diagnostic data.`,
      async () => {
        try {
          await API.deleteAttempt(attemptId, userId);
          await loadDashboardData();
        } catch (err) {
          alert(`Failed to delete attempt: ${err.message}`);
        }
      }
    );
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener("click", () => {
      if (currentAttempts.length === 0) {
        alert("Your session history is already empty.");
        return;
      }

      openConfirmModal(
        "Clear All Session History (समग्र-इतिहास-निष्कासनम्)",
        `Are you sure you want to permanently delete ALL ${currentAttempts.length} pronunciation attempt records? This action cannot be reversed and will reset your analytics.`,
        async () => {
          try {
            await API.clearProgress(userId);
            await loadDashboardData();
          } catch (err) {
            alert(`Failed to clear history: ${err.message}`);
          }
        }
      );
    });
  }

  function openConfirmModal(title, message, onConfirm) {
    confirmModalTitle.textContent = title;
    confirmModalMsg.textContent = message;
    pendingConfirmAction = onConfirm;
    confirmModal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeConfirmModal() {
    confirmModal.style.display = "none";
    document.body.style.overflow = "";
    pendingConfirmAction = null;
  }

  if (confirmBtnClose) confirmBtnClose.addEventListener("click", closeConfirmModal);
  if (confirmBtnCancel) confirmBtnCancel.addEventListener("click", closeConfirmModal);

  if (confirmBtnOk) {
    confirmBtnOk.addEventListener("click", async () => {
      const action = pendingConfirmAction;
      closeConfirmModal();
      if (typeof action === "function") {
        await action();
      }
    });
  }

  if (confirmModal) {
    confirmModal.addEventListener("click", (e) => {
      if (e.target === confirmModal) closeConfirmModal();
    });
  }

  // Helper escape function
  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
