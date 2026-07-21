; Custom NSIS hooks for the PG AI Assistant installer.
; Tauri expands these macros at the matching points of the (un)installer.

; Runs at the end of uninstallation. We use it to optionally remove the
; per-user data directory (%LOCALAPPDATA%\PGAIAssistant), which holds the
; SQLite database (app.db) and secrets.json.
;
; IMPORTANT: during an in-place upgrade (installing a newer version over an
; existing one), Tauri runs the OLD uninstaller SILENTLY before installing the
; new build. We must NOT delete user data in that case, otherwise every upgrade
; would wipe the user's saved connections, API keys and chat history. The
; `IfSilent` guard below ensures the data is only removed on a genuine,
; interactive uninstall.
!macro NSIS_HOOK_POSTUNINSTALL
  ; Skip when running silently (this is the upgrade path) -> keep user data.
  IfSilent pgai_skip_data 0

  MessageBox MB_YESNO|MB_ICONEXCLAMATION \
    "Do you also want to remove your PG AI Assistant data?$\r$\n$\r$\nThis permanently deletes your saved database connections, LLM API keys and chat history. This cannot be undone." \
    IDNO pgai_skip_data

  ; User chose Yes -> remove the whole per-user data folder.
  RMDir /r "$LOCALAPPDATA\PGAIAssistant"

  pgai_skip_data:
!macroend
