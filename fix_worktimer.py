from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Add console.log to WorkTimer useEffect
old_use_effect = '''  useEffect(() => {
    if (timerStart) {'''

new_use_effect = '''  useEffect(() => {
    console.log('WorkTimer useEffect triggered, timerStart:', timerStart);
    if (timerStart) {'''

content = content.replace(old_use_effect, new_use_effect)

# Add console.log to handleStart
old_handle_start = '''  const handleStart = async () => {
    try {
      await onStart();
      // Timer will update from backend response via fetchData
    } catch (error) {'''

new_handle_start = '''  const handleStart = async () => {
    console.log('handleStart called, timerStart prop:', timerStart);
    try {
      await onStart();
      console.log('handleStart after onStart, timerStart prop:', timerStart);
      // Timer will update from backend response via fetchData
    } catch (error) {'''

content = content.replace(old_handle_start, new_handle_start)

file_path.write_text(content, encoding="utf-8")

print("WorkTimer debug logs added.")
