/**
 * Practice Page Controller for VaaniAI
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Elements
  const itemListSelect = document.getElementById("item-select");
  const filterTypeBtns = document.querySelectorAll(".filter-type-btn");
  const targetDeva = document.getElementById("target-deva");
  const targetRoman = document.getElementById("target-roman");
  const targetMeaning = document.getElementById("target-meaning");
  const btnListen = document.getElementById("btn-listen");
  const btnRecord = document.getElementById("btn-record");
  const recordLabel = document.getElementById("record-label");
  const recTimer = document.getElementById("rec-timer");
  const audioPreview = document.getElementById("audio-preview");
  const previewPlayer = document.getElementById("preview-player");
  const btnAnalyze = document.getElementById("btn-analyze");
  const btnDemoTest = document.getElementById("btn-demo-test");
  const loadingOverlay = document.getElementById("loading-overlay");
  const loadingStep = document.getElementById("loading-step");
  const resultContainer = document.getElementById("result-container");
  const micErrorBanner = document.getElementById("mic-error-banner");
  const btnTryAgain = document.getElementById("btn-try-again");
  const btnNextItem = document.getElementById("btn-next-item");
  const forceDemoToggle = document.getElementById("force-demo-toggle");

  // State
  let allItems = [];      // full unfiltered list
  let filteredItems = [];  // filtered view
  let currentItemIndex = 0;
  let currentItem = null;
  let isRecording = false;
  let audioBlob = null;
  let currentFilter = "all";
  let currentAudioUrl = null; // track blob URL for cleanup

  // Preferences from localStorage or defaults
  const userLang = localStorage.getItem("vaani_lang") || "sanskrit";
  const userLevel = localStorage.getItem("vaani_level") || "beginner";
  const userName = localStorage.getItem("vaani_username") || "Arya Sharma";
  const userId = "student_demo";

  // 1. Initialize Sthāna Diagram
  if (typeof SthanaDiagram !== "undefined") {
    SthanaDiagram.init("sthana-diagram-container");
  }

  // 2. Fetch items from API with automatic fallback
  async function loadItems() {
    try {
      let data = await API.getItems(userLevel, userLang);
      allItems = data.items || [];

      // If user level filter returned empty, fetch all items as fallback
      if (allItems.length === 0) {
        data = await API.getItems("", "");
        allItems = data.items || [];
      }

      if (allItems.length > 0) {
        if (micErrorBanner) micErrorBanner.style.display = "none";
        applyFilter();
      } else {
        if (micErrorBanner) {
          micErrorBanner.textContent = "No practice items found. Please run seed.bat to populate the database.";
          micErrorBanner.style.display = "block";
        }
      }
    } catch (err) {
      console.error("Failed to load practice items:", err);
      if (micErrorBanner) {
        micErrorBanner.textContent = "Could not connect to backend server. Make sure the server is running.";
        micErrorBanner.style.display = "block";
      }
    }
  }

  function applyFilter() {
    if (currentFilter === "all") {
      filteredItems = [...allItems];
    } else {
      filteredItems = allItems.filter(item => item.type === currentFilter);
    }
    renderItemOptions();
    if (filteredItems.length > 0) {
      selectItem(0);
    }
  }

  function renderItemOptions() {
    if (!itemListSelect) return;
    itemListSelect.innerHTML = "";

    if (filteredItems.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No items available in this category";
      itemListSelect.appendChild(opt);
      return;
    }

    filteredItems.forEach((item, idx) => {
      const opt = document.createElement("option");
      opt.value = String(idx);
      const typeLabel = item.type === "shloka" ? "श्लोक" : item.type === "word" ? "शब्द" : "वर्ण";
      opt.textContent = `${item.text} — ${item.transliteration} [${typeLabel}]`;
      itemListSelect.appendChild(opt);
    });
  }

  function selectItem(index) {
    if (!filteredItems || filteredItems.length === 0) return;
    if (index < 0 || index >= filteredItems.length) index = 0;
    
    currentItemIndex = index;
    currentItem = filteredItems[index];

    // Update UI text
    if (targetDeva) targetDeva.textContent = currentItem.text;
    if (targetRoman) targetRoman.textContent = currentItem.transliteration;
    if (targetMeaning) targetMeaning.textContent = currentItem.meaning || "";

    // Sync select dropdown
    if (itemListSelect) itemListSelect.value = String(index);

    // Reset recording state and results
    resetRecordingState();
    if (resultContainer) resultContainer.classList.remove("active");

    // Highlight target primary Sthāna on mouth cross-section
    const primarySthana = currentItem.sthana_primary || "kanthya";
    if (typeof SthanaDiagram !== "undefined") {
      SthanaDiagram.highlight(primarySthana);
    }
  }

  function resetRecordingState() {
    isRecording = false;
    audioBlob = null;
    
    // Revoke previous blob URL to prevent memory leaks
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      currentAudioUrl = null;
    }
    
    if (btnRecord) btnRecord.classList.remove("recording");
    if (recordLabel) recordLabel.textContent = "Record";
    if (recTimer) recTimer.textContent = "0.0s";
    if (audioPreview) audioPreview.style.display = "none";
    if (previewPlayer) previewPlayer.src = "";
    if (btnAnalyze) btnAnalyze.style.display = "none";
    if (micErrorBanner) micErrorBanner.style.display = "none";
  }

  // Dropdown change
  if (itemListSelect) {
    itemListSelect.addEventListener("change", (e) => {
      const idx = parseInt(e.target.value, 10);
      if (!isNaN(idx) && idx >= 0 && idx < filteredItems.length) {
        selectItem(idx);
      }
    });
  }

  // Category filter tabs
  filterTypeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterTypeBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.type;
      applyFilter();
    });
  });

  // Reference Audio: Listen Button (uses Web Speech API TTS)
  if (btnListen) {
    btnListen.addEventListener("click", () => {
      if (!currentItem) return;
      btnListen.classList.add("btn-outline");
      btnListen.disabled = true;
      btnListen.innerHTML = `${Icons.speaker("ui-icon")} <span>Playing...</span>`;

      AudioService.playReference(currentItem.text, currentItem.audio_url, () => {
        btnListen.classList.remove("btn-outline");
        btnListen.disabled = false;
        btnListen.innerHTML = `${Icons.speaker("ui-icon")} <span>Listen Reference</span>`;
      });
    });
  }

  // Record Button
  if (btnRecord) {
    btnRecord.addEventListener("click", async () => {
      if (!isRecording) {
        if (micErrorBanner) micErrorBanner.style.display = "none";
        const started = await AudioService.startRecording(
          (timeStr) => {
            if (recTimer) recTimer.textContent = `${timeStr}s`;
          },
          (errorMsg) => {
            showMicError(errorMsg);
          }
        );

        if (started) {
          isRecording = true;
          btnRecord.classList.add("recording");
          if (recordLabel) recordLabel.textContent = "Stop";
          if (audioPreview) audioPreview.style.display = "none";
          if (btnAnalyze) btnAnalyze.style.display = "none";
        }
      } else {
        btnRecord.classList.remove("recording");
        if (recordLabel) recordLabel.textContent = "Record";
        isRecording = false;

        audioBlob = await AudioService.stopRecording();
        if (audioBlob && audioBlob.size > 0) {
          // Clean up old URL
          if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);
          
          currentAudioUrl = URL.createObjectURL(audioBlob);
          if (previewPlayer) {
            previewPlayer.src = currentAudioUrl;
            previewPlayer.load(); // force reload
          }
          if (audioPreview) audioPreview.style.display = "block";
          if (btnAnalyze) btnAnalyze.style.display = "inline-flex";
        } else {
          showMicError("Recording was empty. Please try again and speak clearly into the microphone.");
        }
      }
    });
  }

  function showMicError(message) {
    if (!micErrorBanner) return;
    micErrorBanner.textContent = message;
    micErrorBanner.style.display = "block";
  }

  // Execution pipeline for pronunciation analysis
  async function executeAnalysis(isDemo = false) {
    if (!currentItem) return;

    if (loadingOverlay) loadingOverlay.classList.add("active");
    if (loadingStep) loadingStep.textContent = "Capturing audio waveform...";

    setTimeout(() => {
      if (loadingStep) loadingStep.textContent = "Transcribing phonemes with Google Gemini...";
    }, 600);

    setTimeout(() => {
      if (loadingStep) loadingStep.textContent = "Consulting Pāṇinīya Śikṣā (Sthāna & Prayatna rules)...";
    }, 1500);

    try {
      const formData = new FormData();
      if (audioBlob && audioBlob.size > 0) {
        formData.append("audio", audioBlob, "user_speech.webm");
      }
      formData.append("item_id", currentItem._id);
      formData.append("user_id", userId);

      if (isDemo || (forceDemoToggle && forceDemoToggle.checked)) {
        formData.append("force_demo", "true");
      }

      const result = await API.analyze(formData);
      renderResults(result);

    } catch (err) {
      console.error("Pronunciation analysis error:", err);
      showMicError(`Analysis failed: ${err.message}`);
    } finally {
      if (loadingOverlay) loadingOverlay.classList.remove("active");
    }
  }

  // Button clicks
  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", () => executeAnalysis(false));
  }

  if (btnDemoTest) {
    btnDemoTest.addEventListener("click", () => executeAnalysis(true));
  }

  // Render Result Screen
  function renderResults(result) {
    if (!resultContainer) return;
    resultContainer.classList.add("active");
    resultContainer.scrollIntoView({ behavior: "smooth" });

    // 1. Score Badge
    const scoreVal = result.score || 0;
    const scoreNum = document.getElementById("res-score-num");
    const scoreCircle = document.getElementById("res-score-circle");
    if (scoreNum) scoreNum.textContent = scoreVal;

    if (scoreCircle) {
      scoreCircle.className = "score-badge-circle " + 
        (scoreVal >= 85 ? "score-perfect" : scoreVal >= 60 ? "score-mid" : "score-low");
    }

    // 2. Recognized text display
    const recText = result.recognized_text || "";
    const recTranslit = result.recognized_transliteration || "";

    // 3. Character Breakdown
    const charBoxContainer = document.getElementById("char-breakdown-container");
    if (charBoxContainer) {
      charBoxContainer.innerHTML = "";
      const charResults = result.char_results || [];
      charResults.forEach((cr) => {
        const box = document.createElement("div");
        box.className = `char-box deva-text ${cr.status === "correct" ? "char-correct" : cr.status === "error" ? "char-error" : ""}`;
        box.textContent = cr.char;

        if (cr.status === "error") {
          box.title = `Heard '${cr.heard}' instead of expected '${cr.char}'`;
        } else if (cr.status === "correct") {
          box.title = `Correctly articulated '${cr.char}'`;
        }

        // Clicking a character highlights its Sthana on the diagram
        box.style.cursor = "pointer";
        box.addEventListener("click", () => {
          const soundMeta = cr.feedback?.expected_meta;
          if (soundMeta && soundMeta.sthana && typeof SthanaDiagram !== "undefined") {
            SthanaDiagram.highlight(soundMeta.sthana, soundMeta.sthana_name);
          }
        });

        charBoxContainer.appendChild(box);
      });
    }

    // 4. Shiksha Tips & Paninian Feedback
    const resTipContent = document.getElementById("res-tip-content");
    if (resTipContent) {
      resTipContent.textContent = result.tip || "Pronunciation analyzed successfully.";
    }

    // 5. Demo mode indicator
    if (result.demo_mode) {
      const demoNote = document.createElement("div");
      demoNote.style.cssText = "text-align:center; margin-top:0.5rem; font-size:0.8rem; color:#856404; font-weight:600; display:flex; align-items:center; justify-content:center; gap:0.35rem;";
      demoNote.innerHTML = `${Icons.bolt("ui-icon ui-icon-sm")} <span>Demo Mode — results are pre-computed for reliability</span>`;
      if (charBoxContainer) charBoxContainer.parentElement.insertBefore(demoNote, charBoxContainer.nextSibling);
    }

    // 6. Error Details List
    const errorListContainer = document.getElementById("error-list-container");
    if (errorListContainer) {
      errorListContainer.innerHTML = "";
      const errors = result.errors || [];
      if (errors.length === 0) {
        errorListContainer.innerHTML = `
          <div class="sutra-banner" style="background: var(--status-clean-bg); border-left-color: var(--status-clean);">
            <div class="sutra-title" style="color: var(--status-clean); display: flex; align-items: center; gap: 0.35rem;">
              ${Icons.check("ui-icon ui-icon-sm")} <span>शुद्धोऽयं वर्णः (Accurate Pronunciation)</span>
            </div>
            <div class="sutra-text" style="color: #065F46;">All articulated sounds adhered accurately to Pāṇinian Sthāna and Prayatna. उत्कृष्टम्!</div>
          </div>
        `;
        if (typeof SthanaDiagram !== "undefined") {
          SthanaDiagram.highlight(currentItem.sthana_primary || "kanthya");
        }
      } else {
        errors.forEach((err, idx) => {
          const itemDiv = document.createElement("div");
          itemDiv.className = "error-item";
          itemDiv.innerHTML = `
            <div class="error-title">
              <span class="deva-text" style="display: inline-flex; align-items: center; gap: 0.35rem;">
                <span>दोष ${idx + 1}:</span> <strong>${err.expected_char}</strong> ${Icons.arrowRight("ui-icon ui-icon-sm")} <strong>${err.heard_char}</strong>
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
          
          // Click error item to show comparison on Sthāna Diagram
          itemDiv.style.cursor = "pointer";
          itemDiv.addEventListener("click", () => {
            if (err.expected_sthana && err.heard_sthana && typeof SthanaDiagram !== "undefined") {
              SthanaDiagram.compare(err.expected_sthana, err.heard_sthana);
            }
          });
          
          errorListContainer.appendChild(itemDiv);
        });

        // Show first error on the Sthāna Diagram comparison view!
        const firstErr = errors[0];
        if (firstErr.expected_sthana && firstErr.heard_sthana && typeof SthanaDiagram !== "undefined") {
          SthanaDiagram.compare(firstErr.expected_sthana, firstErr.heard_sthana);
        }
      }
    }
  }

  // Try Again Button
  if (btnTryAgain) {
    btnTryAgain.addEventListener("click", () => {
      resetRecordingState();
      if (resultContainer) resultContainer.classList.remove("active");
      if (currentItem && typeof SthanaDiagram !== "undefined") {
        SthanaDiagram.highlight(currentItem.sthana_primary || "kanthya");
      }
      if (targetDeva) {
        window.scrollTo({ top: targetDeva.offsetTop - 100, behavior: "smooth" });
      }
    });
  }

  // Next Item Button
  if (btnNextItem) {
    btnNextItem.addEventListener("click", () => {
      const nextIdx = (currentItemIndex + 1) % filteredItems.length;
      selectItem(nextIdx);
      if (targetDeva) {
        window.scrollTo({ top: targetDeva.offsetTop - 100, behavior: "smooth" });
      }
    });
  }

  // Initial load
  await loadItems();
});
