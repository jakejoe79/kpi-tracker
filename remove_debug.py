from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Remove debug console.log from startTimer
content = content.replace("    console.log('startTimer called');\n", "")
content = content.replace("      console.log('startTimer response:', response.data);\n", "")
content = content.replace("      console.log('work_timer_start in response:', response.data.work_timer_start);\n", "")

# Remove debug console.log from WorkTimer
content = content.replace("    console.log('WorkTimer useEffect triggered, timerStart:', timerStart);\n", "")
content = content.replace("    console.log('handleStart called, timerStart prop:', timerStart);\n", "")
content = content.replace("      console.log('handleStart after onStart, timerStart prop:', timerStart);\n", "")

file_path.write_text(content, encoding="utf-8")

print("Debug logs removed.")
