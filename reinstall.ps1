Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "mcpv" -Force -ErrorAction SilentlyContinue

uv pip install . --system --reinstall