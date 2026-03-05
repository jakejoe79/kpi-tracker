from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Remove _forceUpdate from startTimer
content = content.replace("      setTodayEntry({ ...response.data, _forceUpdate: Date.now() });", "      setTodayEntry(response.data);")

# Remove _forceUpdate from stopTimer
content = content.replace("      setTodayEntry({ ...response.data, _forceUpdate: Date.now() });", "      setTodayEntry(response.data);")

file_path.write_text(content, encoding="utf-8")

print("_forceUpdate removed.")
