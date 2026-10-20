/**
 * Audio Recording and Speech Synthesis Service for VaaniAI
 */

const AudioService = (function() {
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingStream = null;
  let recordedBlob = null;
  let timerInterval = null;
  let secondsElapsed = 0;

  /**
   * Reference Audio Playback
   * Uses reference audio_url if available, otherwise falls back to browser SpeechSynthesis.
   */
  function playReference(text, audioUrl, onEnd) {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.onended = onEnd || null;
      audio.play().catch(e => {
        console.warn("Direct audio file playback failed, falling back to TTS:", e);
        speakWithTTS(text, onEnd);
      });
      return;
    }
    speakWithTTS(text, onEnd);
  }

  function speakWithTTS(text, onEnd) {
    if (!("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported on this browser.");
      if (onEnd) onEnd();
      return;
    }

    // Cancel ongoing
    window.speechSynthesis.cancel();

    // Clean text for pronunciation (remove "vs")
    const cleanText = text.replace(/vs/gi, "।");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "hi-IN"; // Highest fidelity Indian accent fallback
    utterance.rate = 0.82;   // Slightly slower for distinct phonetic enunciation
    utterance.pitch = 1.0;

    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = (e) => {
      console.warn("TTS error:", e);
      if (onEnd) onEnd();
    };

    window.speechSynthesis.speak(utterance);
  }

  /**
   * Start microphone recording
   */
  async function startRecording(onTimerTick, onError) {
    audioChunks = [];
    recordedBlob = null;
    secondsElapsed = 0;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (onError) onError("Your browser does not support audio recording. Please use modern Chrome, Edge, or Firefox.");
      return false;
    }

    try {
      recordingStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });
    } catch (err) {
      let msg = "Microphone access denied.";
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        msg = "Microphone permission was denied. Please allow microphone permissions in your browser URL bar.";
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        msg = "No microphone hardware found on your system. Please connect a microphone.";
      }
      if (onError) onError(msg);
      return false;
    }

    // Determine supported mime type
    let mimeType = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "audio/webm";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = ""; // Browser default
      }
    }

    try {
      mediaRecorder = mimeType ? new MediaRecorder(recordingStream, { mimeType }) : new MediaRecorder(recordingStream);
    } catch (e) {
      mediaRecorder = new MediaRecorder(recordingStream);
    }

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.start(100); // Collect in 100ms chunks

    // Start timer
    timerInterval = setInterval(() => {
      secondsElapsed += 0.1;
      if (onTimerTick) onTimerTick(secondsElapsed.toFixed(1));
    }, 100);

    return true;
  }

  /**
   * Stop microphone recording
   */
  function stopRecording() {
    return new Promise((resolve) => {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }

      if (!mediaRecorder || mediaRecorder.state === "inactive") {
        resolve(null);
        return;
      }

      mediaRecorder.onstop = () => {
        // Stop all audio tracks
        if (recordingStream) {
          recordingStream.getTracks().forEach(track => track.stop());
          recordingStream = null;
        }

        const mime = mediaRecorder.mimeType || "audio/webm";
        recordedBlob = new Blob(audioChunks, { type: mime });
        resolve(recordedBlob);
      };

      mediaRecorder.stop();
    });
  }

  function getRecordedBlob() {
    return recordedBlob;
  }

  return {
    playReference,
    speakWithTTS,
    startRecording,
    stopRecording,
    getRecordedBlob
  };
})();
