<script lang="ts">
  import DonutProgress from "./lib/DonutProgress.svelte";
  import * as mammoth from "mammoth";
  import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
  import { onMount } from "svelte";

  GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js";

  let tab = "text";

  let title = "";
  let body = "";

  let fileTitle = "";
  let fileBody = "";
  let fileError = "";

  let urlInput = "";
  let urlText = "";
  let urlError = "";

  let loading = false;
  let error = "";
  let result: null | { prediction: string; confidence: number } = null;

  let content = "";

  function changeTab(newTab: string) {
    tab = newTab;
    title = "";
    body = "";
    fileTitle = "";
    fileBody = "";
    fileError = "";
    urlInput = "";
    urlText = "";
    urlError = "";
    error = "";
    result = null;
    loading = false;
  }

  async function predict() {
    loading = true;
    error = "";
    result = null;

    let inputTitle = "";
    let inputBody = "";

    if (tab === "text") {
      inputTitle = title.trim();
      inputBody = body.trim();
    } else if (tab === "file") {
      inputTitle = fileTitle.trim();
      inputBody = fileBody.trim();
      if (!inputTitle || !inputBody) {
        error = "File content is empty or invalid.";
        loading = false;
        return;
      }
    } else if (tab === "url") {
      inputTitle = title.trim();
      inputBody = body.trim();
      if (!inputBody) {
        error = "No text extracted from URL.";
        loading = false;
        return;
      }
    }

    try {
      const res = await fetch("http://localhost:4998/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: inputTitle, body: inputBody }),
      });
      if (!res.ok) throw new Error("Prediction failed");
      result = await res.json();
    } catch (e: any) {
      error = e.message;
    }
    loading = false;
  }

  async function onFileChange(event: Event) {
    fileError = "";
    fileTitle = "";
    fileBody = "";

    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      fileError = "No file selected.";
      return;
    }

    const file = input.files[0];
    const ext = file.name.split(".").pop()?.toLowerCase();

    try {
      if (ext === "txt") {
        const text = await file.text();
        parseTextContent(text);
      } else if (ext === "docx" || ext === "doc") {
        const arrayBuffer = await file.arrayBuffer();
        const { value: docText } = await mammoth.extractRawText({
          arrayBuffer,
        });
        parseTextContent(docText);
      } else if (ext === "pdf") {
        const arrayBuffer = await file.arrayBuffer();
        fileTitle = "";
        fileBody = "";
        const pdfText = await extractPdfText(arrayBuffer);
        parseTextContent(pdfText);
      } else {
        fileError =
          "Unsupported file type. Please upload PDF, Word, or TXT files.";
      }
    } catch (e: any) {
      fileError = "Error reading file: " + e.message;
    }
  }

  function parseTextContent(text: string) {
    const normalized = text.replace(/\s{2,}/g, "\n").trim();

    const lines = normalized
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(
        (line) =>
          line !== "" &&
          !/^\(?\d{4}\)?\s*IEEE/i.test(line) &&
          !/^X{2,}/.test(line) &&
          !/^\d+\/\d+\s*\/\s*\$\d+\.\d{2}/.test(line) &&
          !/^\(?[Cc]opyright\b/i.test(line)
      );

    if (lines.length === 0) {
      fileError = "File is empty.";
      fileTitle = "";
      fileBody = "";
      return;
    }

    fileTitle = lines[0];
    fileBody = lines
      .filter((_, i) => i !== 0)
      .join("\n")
      .trim();
    console.log("Parsed Title:", fileTitle);
    console.log("Parsed Body:", fileBody);
  }

  async function extractPdfText(arrayBuffer: ArrayBuffer): Promise<string> {
    const loadingTask = getDocument({ data: arrayBuffer });
    const pdf = await loadingTask.promise;
    let fullText = "";

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => (item as any).str)
        .join(" ");
      fullText += pageText + "\n\n";
    }
    return fullText;
  }

  async function fetchUrlText() {
    urlError = "";
    title = "";
    body = "";
    loading = true;

    try {
      const response = await fetch(urlInput);
      if (!response.ok) throw new Error("Failed to fetch URL content");

      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      title =
        doc.querySelector("title")?.textContent?.trim() || doc.body.innerText.trim().split("\n")[0] || "No Title";

      body = doc.body.innerText.trim()
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line !== "" && !/^\d{4}\s/.test(line))
        .slice(1) 
        .join("\n");

      if (!body) {
        urlError = "No visible content found on the URL.";
      } else {
        body = body.replace(/\s{2,}/g, "\n").trim();
        if (!body.startsWith(title)) {
          body = `${body}`;
        }
      }
    } catch (e: any) {
      urlError = e.message;
    } finally {
      loading = false;
    }
  }

  $: donutColor = result?.prediction === "hoax" ? "#e3342f" : "#3490dc";
  $: label =
    result?.prediction === "hoax"
      ? "HOAX"
      : result?.prediction === "real"
        ? "REAL"
        : "";
  $: labelBg = result?.prediction === "hoax" ? "#fde8e8" : "#e8f0fd";
  $: labelText = result?.prediction === "hoax" ? "#e3342f" : "#2563eb";
  $: labelBorder = result?.prediction === "hoax" ? "#e3342f44" : "#2563eb44";
</script>

<main>
  <h1>Hoax Detector</h1>
  <div class="tabs">
    <button
      class:active={tab === "text"}
      on:click={() => changeTab("text")}
      type="button"
    >
      Text Input
    </button>
    <button
      class:active={tab === "file"}
      on:click={() => changeTab("file")}
      type="button"
    >
      File Upload
    </button>
    <button
      class:active={tab === "url"}
      on:click={() => changeTab("url")}
      type="button"
    >
      URL Input
    </button>
  </div>

  <div class="card">
    {#if tab === "text"}
      <div class="form-group">
        <label>Judul Artikel</label>
        <input
          type="text"
          bind:value={title}
          placeholder="Masukkan judul berita..."
          autocomplete="off"
        />
      </div>
      <div class="form-group">
        <label>Isi Artikel</label>
        <textarea
          bind:value={body}
          placeholder="Masukkan isi berita..."
          rows="5"
          autocomplete="off"
        ></textarea>
      </div>
      <button
        on:click={predict}
        disabled={loading || !title.trim() || !body.trim()}
      >
        {loading ? "Memprediksi..." : "Prediksi"}
      </button>
    {/if}

    {#if tab === "file"}
      <div class="form-group">
        <label>Upload File (PDF, Word, TXT)</label>
        <input
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          on:change={onFileChange}
        />
      </div>
      {#if fileError}
        <div class="error">{fileError}</div>
      {/if}

      {#if fileTitle || fileBody}
        <div class="file-preview">
          <h3>Preview</h3>
          <div><strong>Title:</strong> {fileTitle}</div>
          <div>
            <strong>Content:</strong>
            <pre>{fileBody}</pre>
          </div>
        </div>
      {/if}

      <button
        on:click={predict}
        disabled={loading || !fileTitle.trim() || !fileBody.trim()}
      >
        {loading ? "Memprediksi..." : "Prediksi"}
      </button>
    {/if}

    {#if tab === "url"}
      <div class="form-group">
        <label>Masukkan URL</label>
        <input
          type="url"
          bind:value={urlInput}
          placeholder="https://example.com/berita"
          autocomplete="off"
        />
      </div>
      <button on:click={fetchUrlText} disabled={loading || !urlInput.trim()}>
        {loading ? "Mengambil teks..." : "Ambil Teks"}
      </button>

      {#if urlError}
        <div class="error">{urlError}</div>
      {/if}

      {#if title || body}
        <div class="file-preview">
          <h3>Preview</h3>
          <div><strong>Title:</strong> {title}</div>
          <div>
            <strong>Content:</strong>
            <pre>{body}</pre>
          </div>
        </div>
         <button
        on:click={predict}
        disabled={loading || !title.trim() || !body.trim()}
      >
        {loading ? "Memprediksi..." : "Prediksi"}
      </button>
      {/if}
    {/if}
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if result}
    <div class="result-card">
      <div class="result">
        <DonutProgress value={result.confidence} color={donutColor} />
        <div
          class="label-badge"
          style="background:{labelBg};color:{labelText};border-color:{labelBorder};"
        >
          {label}
        </div>
        <div class="confidence">
          Confidence: {(result.confidence * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  @import "./style.css";
</style>
