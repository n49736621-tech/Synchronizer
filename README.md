# Synchronizer
# Python 即時同步控制器 (Real-time Window Synchronizer)

這是一個使用 Python 開發的 Windows 桌面應用程式，專為需要同時操作多個相同視窗的情境（例如多開遊戲、重複性資料登錄）而設計。
   *畫面大小需一致
本工具能將使用者在「主控視窗」上的鍵盤與滑鼠操作，即時、一對多地廣播到所有指定的「被控視窗」，大幅提升操作效率。

## 🎥 實際功能演示

[點此觀看實際操作影片](https://youtu.be/9jY_JTHU-nM) 

## 的核心功能

* **圖形化介面 (GUI):** 提供一個獨立的操作面板，包含所有功能按鈕、狀態顯示和選項。
* **動態視窗綁定:** 只需點擊「指定主控」，程式會自動尋找並列出所有「同類型」的被控視窗。
* **即時同步操作:**
    * 同步鍵盤 (可開關)。
    * 同步滑鼠點擊與拖曳 (可開關)。
* **彈性的控制功能:**
    * 提供「開始」、「結束」、「暫停/繼續」按鈕。
    * 支援 `F12` (暫停/繼續) 與 `ESC` (停止) 快捷鍵。
    * 可隨時在列表中勾選或取消要同步的視窗。

## 🛠️ 使用技術

* **Python 3**
* **tkinter:** 用於建構圖形使用者介面 (GUI)。
* **pynput:** 建立全域鍵盤與滑鼠監聽器 (Listener)，以抓取系統層級的輸入事件。
* **pywin32:** 呼叫 Windows API 進行底層視窗操作，包含：
    * `win32gui.WindowFromPoint` / `win32gui.EnumWindows`: 查找並枚舉視窗句柄 (hwnd)。
    * `win32gui.PostMessage`: 向背景視窗發送鍵鼠訊息 (如 `WM_KEYDOWN`, `WM_LBUTTONDOWN`)。
    * `win32gui.ScreenToClient`: 將全螢幕座標轉換為視窗內部相對座標。
* **threading:** 建立獨立執行緒來運行 `pynput` 監聽器，防止 GUI 介面 (Mainloop) 卡死。

## 🚀 如何使用

1.  確保您已安裝 Python 環境。
2.  安裝必要的函式庫：
    ```bash
    pip install pynput pywin32
    ```
3.  執行主程式：
    ```bash
    python jia.py
    ```
4.  點擊 `[1. 指定主控]` 按鈕，然後點擊您的主要操作視窗。
5.  在「被控視窗列表」中勾選您想同步的視窗。
6.  點擊 `[開始同步]` 即可開始。
