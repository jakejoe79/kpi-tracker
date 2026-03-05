from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Remove the setLocalTimerStart line
content = content.replace("      // Sync local timer start with prop\n      setLocalTimerStart(timerStart);\n", "")

# Remove the comment
content = content.replace("      // Sync local timer start with prop\n", "")

file_path.write_text(content, encoding="utf-8")

print("WorkTimer fixed.")
