from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Complete rewrite of WorkTimer component
old_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);
  
  useEffect(() => {
    // Sync local timer start with prop
    setLocalTimerStart(timerStart);
    if (timerStart) {'''

new_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);
  
  useEffect(() => {
    if (timerStart) {'''

content = content.replace(old_worktimer, new_worktimer)

# Also fix handleStart to remove the fetchData comment
old_handle_start = '''  const handleStart = async () => {
    try {
      await onStart();
      // Timer will update from backend response via fetchData
    } catch (error) {'''

new_handle_start = '''  const handleStart = async () => {
    try {
      await onStart();
    } catch (error) {'''

content = content.replace(old_handle_start, new_handle_start)

file_path.write_text(content, encoding="utf-8")

print("WorkTimer completely fixed.")
