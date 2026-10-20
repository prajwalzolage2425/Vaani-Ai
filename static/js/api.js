/**
 * API Client for VaaniAI Backend
 */

const API = {
  baseUrl: "",

  async getHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`);
      return await res.json();
    } catch (err) {
      console.error("Health check error:", err);
      return { status: "offline", error: err.message };
    }
  },

  async getItems(level = "", language = "") {
    const params = new URLSearchParams();
    if (level) params.append("level", level);
    if (language) params.append("language", language);

    const url = `${this.baseUrl}/api/items?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch items (${res.status})`);
    return await res.json();
  },

  async getSound(symbol) {
    const url = `${this.baseUrl}/api/sounds/${encodeURIComponent(symbol)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch sound ${symbol}`);
    return await res.json();
  },

  async getAllSounds() {
    const url = `${this.baseUrl}/api/sounds`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch sounds`);
    return await res.json();
  },

  async analyze(formData) {
    const url = `${this.baseUrl}/api/analyze`;
    const res = await fetch(url, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `Analysis failed (${res.status})`);
    }
    return data;
  },

  async getProgress(userId = "student_demo") {
    const url = `${this.baseUrl}/api/progress/${encodeURIComponent(userId)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch progress for ${userId}`);
    return await res.json();
  },

  async getAttempt(attemptId) {
    const url = `${this.baseUrl}/api/attempts/${encodeURIComponent(attemptId)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch attempt details (${res.status})`);
    return await res.json();
  },

  async deleteAttempt(attemptId, userId = "student_demo") {
    const url = `${this.baseUrl}/api/attempts/${encodeURIComponent(attemptId)}?user_id=${encodeURIComponent(userId)}`;
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `Failed to delete attempt (${res.status})`);
    }
    return await res.json();
  },

  async clearProgress(userId = "student_demo") {
    const url = `${this.baseUrl}/api/progress/${encodeURIComponent(userId)}`;
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `Failed to clear history (${res.status})`);
    }
    return await res.json();
  }
};
