const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (error) {
    throw new Error(`Network request to ${API_BASE}${path} failed. Confirm the FastAPI server is running and CORS allows this origin.`);
  }

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const payload = await response.json();
      message = payload.detail || JSON.stringify(payload);
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return response;
}

export async function uploadStatement(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await request("/api/parse/upload", {
    method: "POST",
    body: formData
  });
  return response.json();
}

export async function analyzeDashboard(payload) {
  const response = await request("/api/dashboard/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return response.json();
}

export async function getAiAnswer(payload, smart = false) {
  const response = await request(smart ? "/api/ai/suggestions" : "/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return response.json();
}

export async function downloadExport(path, payload) {
  const response = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return response.blob();
}
