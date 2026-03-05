from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

# Add console.log to startTimer
old_start_timer = '''  const startTimer = async () => {
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      setTodayEntry(response.data);
      toast.success('Timer started!');
    } catch (error) {'''

new_start_timer = '''  const startTimer = async () => {
    console.log('startTimer called');
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      console.log('startTimer response:', response.data);
      console.log('work_timer_start in response:', response.data.work_timer_start);
      setTodayEntry(response.data);
      toast.success('Timer started!');
    } catch (error) {'''

content = content.replace(old_start_timer, new_start_timer)

file_path.write_text(content, encoding="utf-8")

print("App startTimer debug logs added.")
