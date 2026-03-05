from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

old = """  const stopTimer = async () => {
    try {
      await axios.post(`${API}/entries/${today}/timer/stop`, null, { headers: getAuthHeaders() });
      fetchData();
    } catch (error) {
      toast.error('Failed to stop timer');
    }
  };"""

new = """  const stopTimer = async () => {
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/stop`, null, { headers: getAuthHeaders() });
      setTodayEntry(response.data);
      toast.success('Timer stopped!');
    } catch (error) {
      toast.error('Failed to stop timer');
    }
  };"""

content = content.replace(old, new)
file_path.write_text(content, encoding="utf-8")

print("stopTimer updated.")
