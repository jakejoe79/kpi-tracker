from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Fix WorkTimer to not have its own handleStart/handleStop - just display
old_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);
  const [localTimerStart, setLocalTimerStart] = useState(timerStart);

  useEffect(() => {
    // Sync local timer start with prop
    setLocalTimerStart(timerStart);
    if (timerStart) {'''

new_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (timerStart) {'''

content = content.replace(old_worktimer, new_worktimer)

# Remove the localTimerStart dependency
old_dep = '''  }, [localTimerStart]);'''

new_dep = '''  }, [timerStart]);'''

content = content.replace(old_dep, new_dep)

# Simplify handleStart to just call onStart and let parent update state
old_handle_start = '''  const handleStart = async () => {
    console.log('handleStart called, timerStart prop:', timerStart);
    try {
      await onStart();
      console.log('handleStart after onStart, timerStart prop:', timerStart);
      // Timer will update from backend response via fetchData
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start timer';
      toast.error(errorMessage);
    }
  };'''

new_handle_start = '''  const handleStart = async () => {
    try {
      await onStart();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start timer';
      toast.error(errorMessage);
    }
  };'''

content = content.replace(old_handle_start, new_handle_start)

# Simplify handleStop
old_handle_stop = '''  const handleStop = async () => {
    await onStop();
  };'''

new_handle_stop = '''  const handleStop = async () => {
    await onStop();
  };'''

content = content.replace(old_handle_stop, new_handle_stop)

file_path.write_text(content, encoding="utf-8")

print("WorkTimer simplified.")
