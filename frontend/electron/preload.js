const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('lillith', {
  openExternal: (url) => ipcRenderer.invoke('app:open-external', url),
});
