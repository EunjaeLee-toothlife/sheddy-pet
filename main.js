const { app, BrowserWindow, Menu, Tray, nativeImage, ipcMain } = require("electron");
const path = require("path");

let petWindow;
let tray;
let isQuitting = false;
let clickThrough = false;
let dragEndTimer;
const BASE_WINDOW_HEIGHT = 480;
const BUBBLE_ANCHOR_FROM_BOTTOM = 402;
const BUBBLE_TOP_PADDING = 18;

function send(channel, value) {
  petWindow?.webContents.send(channel, value);
}

function setClickThrough(enabled) {
  clickThrough = enabled;
  petWindow?.setIgnoreMouseEvents(enabled, { forward: true });
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
  const bubbleHeight = Number.isFinite(height) ? Math.max(0, height) : 0;
  const targetHeight = Math.max(
    BASE_WINDOW_HEIGHT,
    Math.min(720, Math.ceil(BUBBLE_ANCHOR_FROM_BOTTOM + bubbleHeight + BUBBLE_TOP_PADDING)),
  );
  const bounds = petWindow.getBounds();
  if (bounds.height === targetHeight) return;
  const bottom = bounds.y + bounds.height;
  petWindow.setBounds({ ...bounds, y: bottom - targetHeight, height: targetHeight }, false);
});

app.whenReady().then(createWindow);
app.on("activate", () => petWindow?.show());
