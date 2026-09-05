const { app, BrowserWindow, Menu, Tray, nativeImage, ipcMain } = require("electron");
const path = require("path");

let petWindow;
let tray;
let isQuitting = false;
let clickThrough = false;
let dragEndTimer;
let petScale = 1;
let bubbleHeight = 0;
const PET_SCALES = [0.75, 1, 1.25, 1.5];
const BASE_WINDOW_WIDTH = 360;
const BASE_WINDOW_HEIGHT = 480;
const BUBBLE_ANCHOR_FROM_BOTTOM = 402;
const BUBBLE_TOP_PADDING = 18;
const MAX_WINDOW_HEIGHT = 720;

function send(channel, value) {
  petWindow?.webContents.send(channel, value);
}

function setClickThrough(enabled) {
  clickThrough = enabled;
  petWindow?.setIgnoreMouseEvents(enabled, { forward: true });
  refreshTrayMenu();
}

function resizePetWindow() {
  if (!petWindow) return;
  const width = Math.round(BASE_WINDOW_WIDTH * petScale);
  const baseHeight = Math.round(BASE_WINDOW_HEIGHT * petScale);
  const height = Math.max(
    baseHeight,
    Math.min(
      Math.round(MAX_WINDOW_HEIGHT * petScale),
      Math.ceil((BUBBLE_ANCHOR_FROM_BOTTOM + BUBBLE_TOP_PADDING) * petScale + bubbleHeight),
    ),
  );
  const bounds = petWindow.getBounds();
  if (bounds.width === width && bounds.height === height) return;
  const centerX = bounds.x + bounds.width / 2;
  const bottom = bounds.y + bounds.height;
  petWindow.setBounds({
    x: Math.round(centerX - width / 2),
    y: bottom - height,
    width,
    height,
  }, false);
}

function setPetScale(scale) {
  if (!PET_SCALES.includes(scale)) return;
  petScale = scale;
  resizePetWindow();
  send("pet:scale", scale);
  refreshTrayMenu();
}

function refreshTrayMenu() {
  if (!tray) return;
  const menu = Menu.buildFromTemplate([
    { label: petWindow?.isVisible() ? "Hide Desk Toy" : "Show Desk Toy", click: () => petWindow?.isVisible() ? petWindow.hide() : petWindow?.show() },
    { label: "Say something", click: () => send("pet:speak") },
    {
      label: "Speech frequency",
      submenu: [
        { label: "Every 5–15 minutes", click: () => send("pet:speech-mode", "normal") },
        { label: "Every 15–30 minutes", click: () => send("pet:speech-mode", "rare") },
        { label: "Off", click: () => send("pet:speech-mode", "off") },
      ],
    },
    {
      label: "Pet size",
      submenu: PET_SCALES.map(scale => ({
        label: `${Math.round(scale * 100)}%`,
        type: "radio",
        checked: petScale === scale,
        click: () => setPetScale(scale),
      })),
    },
    { type: "separator" },
    { label: clickThrough ? "Disable click-through" : "Enable click-through", click: () => setClickThrough(!clickThrough) },
    { type: "separator" },
    { label: "Quit", click: () => { isQuitting = true; app.quit(); } },
  ]);
  menu.on("menu-will-close", () => {
    setImmediate(() => petWindow?.setAlwaysOnTop(true, "floating"));
  });
  tray.setContextMenu(menu);
}

function createWindow() {
  petWindow = new BrowserWindow({
    width: 360,
    height: 480,
    transparent: true,
    frame: false,
    resizable: false,
    alwaysOnTop: true,
    hasShadow: false,
    webPreferences: { contextIsolation: true, nodeIntegration: false, preload: path.join(__dirname, "preload.js") },
  });
  petWindow.setAlwaysOnTop(true, "floating");
  petWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  petWindow.loadFile(path.join(__dirname, "widget.html"), { query: { desktop: "1" } });
  petWindow.on("close", event => {
    if (!isQuitting) { event.preventDefault(); petWindow.hide(); refreshTrayMenu(); }
  });
  petWindow.on("show", refreshTrayMenu);
  petWindow.on("hide", refreshTrayMenu);
  petWindow.on("will-move", () => {
    clearTimeout(dragEndTimer);
    send("pet:drag-start");
  });
  petWindow.on("move", () => {
    clearTimeout(dragEndTimer);
    dragEndTimer = setTimeout(() => send("pet:drag-end"), 150);
  });

  const icon = nativeImage.createFromPath(path.join(__dirname, "assets", "icons", "tray-icon.png")).resize({ width: 18, height: 18 });
  if (process.platform === "darwin") icon.setTemplateImage(true);
  tray = new Tray(icon);
  tray.setToolTip("Desk Toy");
  tray.on("click", () => {
    if (!petWindow.isVisible()) petWindow.show();
  });
  refreshTrayMenu();
}

ipcMain.on("pet:bubble-height", (event, height) => {
  if (!petWindow || event.sender !== petWindow.webContents) return;
  bubbleHeight = Number.isFinite(height) ? Math.max(0, height) : 0;
  resizePetWindow();
});

ipcMain.on("pet:set-scale", (event, scale) => {
  if (!petWindow || event.sender !== petWindow.webContents) return;
  setPetScale(scale);
});

app.whenReady().then(createWindow);
app.on("activate", () => petWindow?.show());
