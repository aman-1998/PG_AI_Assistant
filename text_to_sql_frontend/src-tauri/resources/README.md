# Bundled Python sidecars are copied here at build time (see the desktop-release
# workflow). The onedir folders themselves are git-ignored because they are large
# build artifacts:
#   resources/pg-ai-backend/   (PyInstaller output of the FastAPI backend)
#   resources/pg-ai-mcp/       (PyInstaller output of the MCP server)
