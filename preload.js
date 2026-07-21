const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("deskPet", {
  onSpeak: callback => ipcRenderer.on("pet:speak", () => callback()),
  onSpeechMode: callback => ipcRenderer.on("pet:speech-mode", (_, mode) => callback(mode)),
  onDragStart: callback => ipcRenderer.on("pet:drag-start", () => callback()),
  onDragEnd: callback => ipcRenderer.on("pet:drag-end", () => callback()),
  setBubbleHeight: height => ipcRenderer.send("pet:bubble-height", height),
});
