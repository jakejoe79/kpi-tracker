import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { AlertCircle, Calendar, TrendingUp } from 'lucide-react';

/**
 * GoalHistory Component
 * Shows historical goals and how they've evolved based on performance metrics
 */
export function GoalHistory({ userId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [startDate, setStartDate] = useState(getDefaultStartDate());
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  function getDefaultStartDate() {
    const date = new Date();
    date.setDate(date.getDate() - 30); // Last 30 days
    return date.toISOString().split('T')[0];
  }

  useEffect(() => {
    fetchGoalsHistory();
  }, [userId]);

  const fetchGoalsHistory = async (start = startDate, end = endDate) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/goals/history?start_date=${start}&end_date=${end}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch goals history');
      }

      const data = await response.json();
      setHistory(data.goals || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching goals history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDateRangeChange = () => {
    fetchGoalsHistory(startDate, endDate);
  };

  const getPeriodTypeLabel = (periodType) => {
    const labels = {
      'daily': 'Daily',
      'weekly': 'Weekly',
      'biweekly': 'Biweekly'
    };
    return labels[periodType] || periodType;
  };

  const getPeriodTypeBadgeColor = (periodType) => {
    const colors = {
      'daily': 'bg-blue-100 text-blue-800',
      'weekly': 'bg-purple-100 text-purple-800',
      'biweekly': 'bg-green-100 text-green-800'
    };
    return colors[periodType] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (value) => {
    return `$${parseFloat(value).toFixed(2)}`;
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Error loading goals history: {error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Goal History</CardTitle>
        <CardDescription>
          View how your goals have evolved based on your performance metrics
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Date Range Filter */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start_date" className="text-sm font-medium">
              Start Date
            </Label>
            <Input
              id="start_date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="end_date" className="text-sm font-medium">
              End Date
            </Label>
            <Input
              id="end_date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <div className="flex items-end">
            <Button
              onClick={handleDateRangeChange}
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Loading...' : 'Filter'}
            </Button>
          </div>
        </div>

        {/* History Table */}
        {history.length === 0 ? (
          <Alert>
            <Calendar className="h-4 w-4" />
            <AlertDescription>
              No goal history found for the selected date range.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Profit Target</TableHead>
                  <TableHead>Calls Needed</TableHead>
                  <TableHead>Reservations</TableHead>
                  <TableHead>Time Needed</TableHead>
                  <TableHead>Metrics</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((goal, index) => (
                  <TableRow key={index} className="hover:bg-gray-50">
                    <TableCell className="font-medium">
                      {formatDate(goal.effective_date)}
                    </TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getPeriodTypeBadgeColor(goal.period_type)}`}>
                        {getPeriodTypeLabel(goal.period_type)}
                      </span>
                    </TableCell>
                    <TableCell className="font-semibold">
                      {formatCurrency(goal.profit_target)}
                    </TableCell>
                    <TableCell>
                      {goal.calls_needed}
                    </TableCell>
                    <TableCell>
                      {goal.reservations_needed}
                    </TableCell>
                    <TableCell>
                      {Math.round(goal.time_needed_minutes / 60)}h {Math.round(goal.time_needed_minutes % 60)}m
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => showMetricsDetails(goal)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                      >
                        <TrendingUp className="h-3 w-3" />
                        View
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Summary Stats */}
        {history.length > 0 && (
          <Card className="bg-gray-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Summary</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Records:</span>
                <span className="font-medium">{history.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Profit Target:</span>
                <span className="font-medium">
                  {formatCurrency(
                    history.reduce((sum, g) => sum + g.profit_target, 0) / history.length
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Booking Speed:</span>
                <span className="font-medium">
                  {(history.reduce((sum, g) => sum + g.booking_speed_interval, 0) / history.length).toFixed(1)} min
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Conversion Rate:</span>
                <span className="font-medium">
                  {(history.reduce((sum, g) => sum + g.conversion_rate, 0) / history.length).toFixed(1)}%
                </span>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}

function showMetricsDetails(goal) {
  // This would typically open a modal or expand a details section
  const details = `
Period: ${goal.period_type}
Date: ${goal.effective_date}

Profit Target: $${goal.profit_target.toFixed(2)}
Calls Needed: ${goal.calls_needed}
Reservations Needed: ${goal.reservations_needed}
Time Needed: ${Math.round(goal.time_needed_minutes / 60)}h ${Math.round(goal.time_needed_minutes % 60)}m

Metrics Used:
- Booking Speed: ${goal.booking_speed_interval.toFixed(1)} min/booking
- Conversion Rate: ${goal.conversion_rate.toFixed(1)}%
- Avg Profit/Booking: $${goal.avg_profit_per_booking.toFixed(2)}
  `;
  alert(details);
}

export default GoalHistory;
