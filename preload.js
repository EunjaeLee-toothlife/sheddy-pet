const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("deskPet", {
  onSpeak: callback => ipcRenderer.on("pet:speak", () => callback()),
  onSpeechMode: callback => ipcRenderer.on("pet:speech-mode", (_, mode) => callback(mode)),
  onDragStart: callback => ipcRenderer.on("pet:drag-start", () => callback()),
  onDragEnd: callback => ipcRenderer.on("pet:drag-end", () => callback()),
  onScale: callback => ipcRenderer.on("pet:scale", (_, scale) => callback(scale)),
  setBubbleHeight: height => ipcRenderer.send("pet:bubble-height", height),
  setScale: scale => ipcRenderer.send("pet:set-scale", scale),
});
