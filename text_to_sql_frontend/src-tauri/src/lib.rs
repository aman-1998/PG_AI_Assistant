use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::path::BaseDirectory;
use tauri::Manager;

/// Fixed local ports the bundled Python services listen on.
const BACKEND_PORT: u16 = 8010;
const MCP_PORT: u16 = 8020;

/// Holds the spawned sidecar processes so they can be killed on exit.
struct Sidecars(Mutex<Vec<Child>>);

/// Path to the shared secrets store, computed to match the Python services'
/// `platformdirs.user_data_dir("PGAIAssistant", appauthor=False)/secrets.json`
/// exactly on each OS (Tauri's own app_data_dir uses the bundle identifier and
/// would point elsewhere).
fn secrets_file_path() -> Option<PathBuf> {
    let base: PathBuf = if cfg!(windows) {
        PathBuf::from(std::env::var_os("LOCALAPPDATA")?)
    } else if cfg!(target_os = "macos") {
        PathBuf::from(std::env::var_os("HOME")?)
            .join("Library")
            .join("Application Support")
    } else {
        match std::env::var_os("XDG_DATA_HOME") {
            Some(x) if !x.is_empty() => PathBuf::from(x),
            _ => PathBuf::from(std::env::var_os("HOME")?)
                .join(".local")
                .join("share"),
        }
    };
    Some(base.join("PGAIAssistant").join("secrets.json"))
}

/// 32 random bytes, hex-encoded - a strong passphrase for the shared token secret.
fn generate_secret() -> String {
    let mut buf = [0u8; 32];
    getrandom::getrandom(&mut buf).expect("OS RNG unavailable");
    buf.iter().map(|b| format!("{b:02x}")).collect()
}

/// Return the shared `DB_CONNECTION_TOKEN_SECRET`, reading it from the shared
/// secrets.json if present, otherwise generating and persisting it (preserving
/// any other keys the Python services store there). Resolving it here - once,
/// before either sidecar starts - and injecting it into both guarantees the
/// backend and MCP server always agree on the key used to encrypt/decrypt the
/// per-request DB connection token (otherwise a first-launch race between the
/// two processes generating their own secrets causes "Invalid padding bytes").
fn resolve_shared_token_secret() -> Option<String> {
    let path = secrets_file_path()?;
    let mut data: serde_json::Map<String, serde_json::Value> = match std::fs::read_to_string(&path)
    {
        Ok(contents) => serde_json::from_str(&contents).unwrap_or_default(),
        Err(_) => serde_json::Map::new(),
    };
    if let Some(existing) = data
        .get("DB_CONNECTION_TOKEN_SECRET")
        .and_then(|v| v.as_str())
    {
        if !existing.is_empty() {
            return Some(existing.to_string());
        }
    }
    let secret = generate_secret();
    data.insert(
        "DB_CONNECTION_TOKEN_SECRET".to_string(),
        serde_json::Value::String(secret.clone()),
    );
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).ok();
    }
    if let Ok(serialized) = serde_json::to_string_pretty(&data) {
        std::fs::write(&path, serialized).ok();
    }
    Some(secret)
}

/// Platform-specific executable name for a PyInstaller onedir binary.
fn exe_name(base: &str) -> String {
    if cfg!(windows) {
        format!("{base}.exe")
    } else {
        base.to_string()
    }
}

/// Block until `127.0.0.1:port` accepts a TCP connection or the timeout elapses.
fn wait_for_port(port: u16, timeout: Duration) -> bool {
    let addr = format!("127.0.0.1:{port}");
    let start = Instant::now();
    while start.elapsed() < timeout {
        if TcpStream::connect(&addr).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(300));
    }
    false
}

/// Spawn a bundled Python service (PyInstaller onedir) as a child process.
///
/// `folder` is the resource sub-directory, `bin` the executable base name.
/// The child's working directory is set to a writable per-user data dir so the
/// MCP server can create its relative output folders (exports, diagrams, ...).
fn spawn_sidecar(
    app: &tauri::App,
    folder: &str,
    bin: &str,
    port: u16,
    extra_env: &[(&str, String)],
) -> std::io::Result<Child> {
    let exe = app
        .path()
        .resolve(
            format!("{folder}/{}", exe_name(bin)),
            BaseDirectory::Resource,
        )
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::NotFound, e.to_string()))?;

    let workdir = app
        .path()
        .app_data_dir()
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::NotFound, e.to_string()))?;
    std::fs::create_dir_all(&workdir).ok();

    let mut cmd = Command::new(&exe);
    cmd.current_dir(&workdir)
        .env("HOST", "127.0.0.1")
        .env("PORT", port.to_string());
    for (k, v) in extra_env {
        cmd.env(k, v);
    }

    // Do not pop up a console window for each Python service on Windows.
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    cmd.spawn()
}

fn start_sidecars(app: &tauri::App) {
    // The webview runs from the Tauri origin, so the backend must allow it via CORS.
    let cors =
        "http://tauri.localhost,tauri://localhost,https://tauri.localhost,http://localhost:5173"
            .to_string();

    // Shared secret both processes use to encrypt/decrypt the DB connection token.
    // Resolved once here so the backend and MCP server never diverge.
    let token_secret = resolve_shared_token_secret();
    if token_secret.is_none() {
        log::error!("could not resolve shared DB_CONNECTION_TOKEN_SECRET; sidecars will fall back to their own generation");
    }

    let mut backend_env = vec![
        ("CORS_ORIGINS", cors),
        ("MCP_SERVER_URL", format!("http://127.0.0.1:{MCP_PORT}/mcp")),
    ];
    let mut mcp_env: Vec<(&str, String)> = Vec::new();
    if let Some(secret) = &token_secret {
        backend_env.push(("DB_CONNECTION_TOKEN_SECRET", secret.clone()));
        mcp_env.push(("DB_CONNECTION_TOKEN_SECRET", secret.clone()));
    }

    let backend = spawn_sidecar(
        app,
        "pg-ai-backend",
        "pg-ai-backend",
        BACKEND_PORT,
        &backend_env,
    );
    let mcp = spawn_sidecar(app, "pg-ai-mcp", "pg-ai-mcp", MCP_PORT, &mcp_env);

    let state = app.state::<Sidecars>();
    let mut guard = state.0.lock().expect("sidecar lock");
    match mcp {
        Ok(child) => guard.push(child),
        Err(e) => log::error!("failed to start MCP sidecar: {e}"),
    }
    match backend {
        Ok(child) => guard.push(child),
        Err(e) => log::error!("failed to start backend sidecar: {e}"),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .manage(Sidecars(Mutex::new(Vec::new())))
        .setup(|app| {
            start_sidecars(app);

            // Keep the window hidden until the backend is accepting connections,
            // then reveal it so the first page load succeeds.
            let handle = app.handle().clone();
            std::thread::spawn(move || {
                wait_for_port(BACKEND_PORT, Duration::from_secs(90));
                if let Some(win) = handle.get_webview_window("main") {
                    let _ = win.show();
                    let _ = win.set_focus();
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } = &event {
                if let Some(state) = app_handle.try_state::<Sidecars>() {
                    if let Ok(mut guard) = state.0.lock() {
                        for child in guard.iter_mut() {
                            let _ = child.kill();
                        }
                        guard.clear();
                    }
                }
            }
        });
}
