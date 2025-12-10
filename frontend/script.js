const uploadForm = document.getElementById("upload-form");
const uploadBtn = document.getElementById("upload-btn");
const pdfInput = document.getElementById("pdf-file");
const uploadStatusEl = document.getElementById("upload-status");
const activeFileEl = document.getElementById("active-file");

const form = document.getElementById("ask-form");
const questionInput = document.getElementById("question");
const askBtn = document.getElementById("ask-btn");

const statusEl = document.getElementById("status");
const answerContainer = document.getElementById("answer-container");
const answerText = document.getElementById("answer-text");

let hasActivePdf = false;

/* ---------- Load status on page load ---------- */
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    hasActivePdf = !!data.has_pdf;
    if (data.file_name) {
      activeFileEl.textContent = `Active document: ${data.file_name}`;
    } else {
      activeFileEl.textContent = "No document loaded yet.";
    }
  } catch {
    // ignore
  }
});

/* ---------- Upload form handler ---------- */
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = pdfInput.files[0];
  if (!file) {
    uploadStatusEl.textContent = "Please select a PDF file.";
    return;
  }

  uploadBtn.disabled = true;
  uploadStatusEl.textContent = "Uploading and indexing PDF...";
  activeFileEl.textContent = "";
  statusEl.textContent = "";
  answerContainer.classList.add("hidden");
  answerText.textContent = "";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      uploadStatusEl.textContent = "Error: " + (data.error || "Upload failed");
      hasActivePdf = false;
      return;
    }

    uploadStatusEl.textContent = data.message || "Upload successful.";
    if (data.file_name) {
      activeFileEl.textContent = `Active document: ${data.file_name}`;
    }
    hasActivePdf = true;
  } catch (err) {
    console.error(err);
    uploadStatusEl.textContent = "Error: " + err.message;
    hasActivePdf = false;
  } finally {
    uploadBtn.disabled = false;
  }
});

/* ---------- Question form handler ---------- */
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = questionInput.value.trim();
  if (!question) {
    statusEl.textContent = "Please type a question.";
    return;
  }

  if (!hasActivePdf) {
    statusEl.textContent = "Please upload a PDF first.";
    return;
  }

  askBtn.disabled = true;
  statusEl.textContent = "Thinking...";
  answerContainer.classList.add("hidden");
  answerText.textContent = "";

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();

    if (!response.ok) {
      statusEl.textContent = "Error: " + (data.error || "Server error");
      return;
    }

    statusEl.textContent = "";

    if (data.file_name) {
      activeFileEl.textContent = `Active document: ${data.file_name}`;
      hasActivePdf = true;
    }

    if (data.answer) {
      answerText.textContent = data.answer;
      answerContainer.classList.remove("hidden");
    } else {
      answerText.textContent = "No answer returned.";
      answerContainer.classList.remove("hidden");
    }
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Error: " + err.message;
  } finally {
    askBtn.disabled = false;
  }
});
