from pathlib import Path

file_path = Path("repos/kpi/kpi-tracker-main/frontend/src/App.js")
content = file_path.read_text(encoding="utf-8")

old = """  const startTimer = async () => {
    try {
      await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      fetchData();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start timer';
      toast.error(errorMessage);
    }
  };"""

new = """  const startTimer = async () => {
    try {
      const response = await axios.post(`${API}/entries/${today}/timer/start`, null, { headers: getAuthHeaders() });
      setTodayEntry(response.data);
      toast.success('Timer started!');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start timer';
      toast.error(errorMessage);
    }
  };"""

content = content.replace(old, new)
file_path.write_text(content, encoding="utf-8")

print("startTimer updated.")
