/**
 * Windows 95 Modal Dialogs & Window Controls
 */

import { state } from "./state.js";

export function initDialogs() {
  const modalOpen = document.getElementById("modal-open");
  const modalSave = document.getElementById("modal-save");
  const modalAbout = document.getElementById("modal-about");

  const fileListContainer = document.getElementById("file-list-container");
  const btnOpenConfirm = document.getElementById("btn-modal-open-confirm");
  const inpSaveFilename = document.getElementById("inp-save-filename");
  const inpSaveTitle = document.getElementById("inp-save-title");
  const btnSaveConfirm = document.getElementById("btn-modal-save-confirm");

  const windowTitleText = document.getElementById("window-title-text");

  let selectedFileToOpen = null;

  function showModal(modal) {
    if (modal) modal.classList.add("show");
  }

  function hideModal(modal) {
    if (modal) modal.classList.remove("show");
  }

  // Close buttons
  document.querySelectorAll(".modal-close-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      hideModal(document.getElementById(targetId));
    });
  });

  // Open Dialog logic
  async function openFileDialog() {
    fileListContainer.innerHTML = '<div style="padding: 6px; color: #808080;">Loading sequences...</div>';
    selectedFileToOpen = null;
    btnOpenConfirm.disabled = true;
    showModal(modalOpen);

    try {
      const resp = await fetch("/api/sequences");
      if (!resp.ok) throw new Error("Failed to load list");
      const list = await resp.json();

      if (list.length === 0) {
        fileListContainer.innerHTML = '<div style="padding: 6px; color: #808080;">No saved sequences found.</div>';
        return;
      }

      fileListContainer.innerHTML = "";
      list.forEach(item => {
        const row = document.createElement("div");
        row.style.padding = "3px 6px";
        row.style.cursor = "pointer";
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.fontSize = "11px";

        row.innerHTML = `
          <span>📄 <strong>${item.name || item.filename}</strong></span>
          <span style="color: #666; font-size: 10px;">${item.step_count} steps (${item.filename})</span>
        `;

        row.addEventListener("click", () => {
          Array.from(fileListContainer.children).forEach(c => {
            c.style.backgroundColor = "";
            c.style.color = "";
          });
          row.style.backgroundColor = "var(--win-selection-bg)";
          row.style.color = "var(--win-selection-text)";
          selectedFileToOpen = item.filename;
          btnOpenConfirm.disabled = false;
        });

        row.addEventListener("dblclick", () => {
          selectedFileToOpen = item.filename;
          confirmLoadFile();
        });

        fileListContainer.appendChild(row);
      });
    } catch (err) {
      fileListContainer.innerHTML = `<div style="padding: 6px; color: red;">Error: ${err.message}</div>`;
    }
  }

  async function confirmLoadFile() {
    if (!selectedFileToOpen) return;
    try {
      const resp = await fetch(`/api/sequences/${selectedFileToOpen}`);
      if (!resp.ok) throw new Error("Failed to fetch sequence file");
      const data = await resp.json();
      state.setSequence(data, selectedFileToOpen);
      if (windowTitleText) {
        windowTitleText.textContent = `WLED Pattern Sequencer - [${selectedFileToOpen}]`;
      }
      hideModal(modalOpen);
    } catch (err) {
      alert(`Could not load sequence: ${err.message}`);
    }
  }

  btnOpenConfirm.addEventListener("click", confirmLoadFile);

  // Save Dialog logic
  function openSaveDialog() {
    inpSaveFilename.value = state.filename || "my_sequence.json";
    inpSaveTitle.value = state.sequence.name || "My Sequence";
    showModal(modalSave);
  }

  async function confirmSaveFile() {
    const filename = inpSaveFilename.value.trim() || "my_sequence.json";
    state.sequence.name = inpSaveTitle.value.trim() || "Untitled";

    try {
      const resp = await fetch("/api/sequences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.sequence)
      });
      if (!resp.ok) throw new Error("Failed to save sequence");
      const res = await resp.json();
      state.filename = res.filename;
      if (windowTitleText) {
        windowTitleText.textContent = `WLED Pattern Sequencer - [${res.filename}]`;
      }
      hideModal(modalSave);
      const statusMsg = document.getElementById("status-message");
      if (statusMsg) statusMsg.textContent = `Saved sequence to ${res.filename}`;
    } catch (err) {
      alert(`Could not save sequence: ${err.message}`);
    }
  }

  btnSaveConfirm.addEventListener("click", confirmSaveFile);

  // New sequence
  function newSequence() {
    state.setSequence({
      name: "New Sequence",
      description: "",
      author: "",
      loop_mode: "infinite",
      loop_count: 1,
      time_dilation: 1.0,
      steps: [
        {
          id: `step_${Date.now()}`,
          name: "Intro Wave",
          target_layer: 0,
          pattern_id: "wave",
          primary_color: "#0088FF",
          palette: "ocean",
          speed: 1.0,
          brightness: 1.0,
          blend_mode: "OVERWRITE",
          channels: null,
          target_opacity: 1.0,
          hold_duration_sec: 4.0,
          transition_sec: 1.0
        }
      ]
    }, "untitled.json");
    if (windowTitleText) {
      windowTitleText.textContent = "WLED Pattern Sequencer - [untitled.json]";
    }
  }

  // Menu bar & Toolbar hooks
  document.getElementById("menu-new").addEventListener("click", newSequence);
  document.getElementById("tb-new").addEventListener("click", newSequence);

  document.getElementById("menu-open").addEventListener("click", openFileDialog);
  document.getElementById("tb-open").addEventListener("click", openFileDialog);

  document.getElementById("menu-save").addEventListener("click", () => {
    if (state.filename && state.filename !== "untitled.json") {
      confirmSaveFile();
    } else {
      openSaveDialog();
    }
  });
  document.getElementById("tb-save").addEventListener("click", openSaveDialog);
  document.getElementById("menu-save-as").addEventListener("click", openSaveDialog);

  document.getElementById("menu-about").addEventListener("click", () => showModal(modalAbout));

  // Window titlebar buttons
  const mainWindow = document.getElementById("main-window");
  let isMaximized = false;
  document.getElementById("btn-maximize").addEventListener("click", () => {
    isMaximized = !isMaximized;
    if (isMaximized) {
      mainWindow.style.maxWidth = "100vw";
      mainWindow.style.height = "100vh";
      mainWindow.style.maxHeight = "100vh";
    } else {
      mainWindow.style.maxWidth = "1100px";
      mainWindow.style.height = "94vh";
      mainWindow.style.maxHeight = "820px";
    }
  });

  document.getElementById("btn-close").addEventListener("click", () => {
    if (confirm("Reset current sequence workspace?")) {
      newSequence();
    }
  });
}
