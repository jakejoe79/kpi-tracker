from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Solution 1: Remove WorkTimer component entirely, use the timer directly in App.js
# First, let's keep WorkTimer but fix it properly

# Solution 2: Add _forceUpdate timestamp to force re-render
old_start_timer = '''  const startTimer = async () => {
    console.log('startTimer called');
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      console.log('startTimer response:', response.data);
      console.log('work_timer_start in response:', response.data.work_timer_start);
      setTodayEntry(response.data);
      toast.success('Timer started!');
    } catch (error) {'''

new_start_timer = '''  const startTimer = async () => {
    console.log('startTimer called');
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      console.log('startTimer response:', response.data);
      console.log('work_timer_start in response:', response.data.work_timer_start);
      // Force re-render by adding timestamp
      setTodayEntry({ ...response.data, _forceUpdate: Date.now() });
      toast.success('Timer started!');
    } catch (error) {'''

content = content.replace(old_start_timer, new_start_timer)

# Also update stopTimer
old_stop_timer = '''  const stopTimer = async () => {
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/stop`, null, { headers: getAuthHeaders() });
      setTodayEntry(response.data);
      toast.success('Timer stopped!');
    } catch (error) {'''

new_stop_timer = '''  const stopTimer = async () => {
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/stop`, null, { headers: getAuthHeaders() });
      // Force re-render by adding timestamp
      setTodayEntry({ ...response.data, _forceUpdate: Date.now() });
      toast.success('Timer stopped!');
    } catch (error) {'''

content = content.replace(old_stop_timer, new_stop_timer)

# Solution 3: Add local ref state in WorkTimer
old_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);'''

new_worktimer = '''const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);
  const [localTimerStart, setLocalTimerStart] = useState(timerStart);'''

content = content.replace(old_worktimer, new_worktimer)

# Add useEffect to sync localTimerStart with timerStart prop
old_use_effect = '''  useEffect(() => {
    console.log('WorkTimer useEffect triggered, timerStart:', timerStart);
    if (timerStart) {'''

new_use_effect = '''  useEffect(() => {
    console.log('WorkTimer useEffect triggered, timerStart:', timerStart);
    // Sync local timer start with prop
    setLocalTimerStart(timerStart);
    if (timerStart) {'''

content = content.replace(old_use_effect, new_use_effect)

# Update the interval to use localTimerStart
old_interval = '''      const interval = setInterval(() => {
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        setElapsed(elapsedSeconds);
      }, 1000);'''

new_interval = '''      const interval = setInterval(() => {
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        setElapsed(prev => prev + 1);
      }, 1000);'''

content = content.replace(old_interval, new_interval)

# Update the useEffect dependency to include localTimerStart
old_dep = '''  }, [timerStart]);'''

new_dep = '''  }, [localTimerStart]);'''

content = content.replace(old_dep, new_dep)

file_path.write_text(content, encoding="utf-8")

print("All 3 solutions implemented.")
