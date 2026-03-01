import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AlertCircle, TrendingUp, Clock, Target } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';

/**
 * GoalDisplay Component
 * Shows current goals for daily/weekly/biweekly periods with progress tracking
 */
export function GoalDisplay({ userId }) {
  const [goals, setGoals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('daily');

  useEffect(() => {
    fetchCurrentGoals();
    // Refresh every 5 minutes
    const interval = setInterval(fetchCurrentGoals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [userId]);

  const fetchCurrentGoals = async () => {
    try {
      const response = await fetch('/api/goals/current', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch goals');
      }
      
      const data = await response.json();
      setGoals(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPaceIndicator = (progressPercent) => {
    if (progressPercent >= 100) {
      return { label: 'Completed', color: 'bg-green-500', textColor: 'text-green-700' };
    } else if (progressPercent >= 75) {
      return { label: 'On Track', color: 'bg-blue-500', textColor: 'text-blue-700' };
    } else if (progressPercent >= 50) {
      return { label: 'Moderate', color: 'bg-yellow-500', textColor: 'text-yellow-700' };
    } else {
      return { label: 'Behind', color: 'bg-red-500', textColor: 'text-red-700' };
    }
  };

  const formatTime = (minutes) => {
    if (minutes < 60) {
      return `${Math.round(minutes)} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const renderGoalCard = (periodType, goalData) => {
    if (!goalData) {
      return (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No goals set for {periodType} period. Please set profit targets.
          </AlertDescription>
        </Alert>
      );
    }

    const pace = getPaceIndicator(goalData.progress_percent);
    const timeRemainingHours = goalData.time_remaining_minutes / 60;

    return (
      <div className="space-y-6">
        {/* Profit Target */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Profit Target</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${goalData.profit_target.toFixed(2)}</div>
              <p className="text-xs text-gray-500 mt-1">
                Current: ${goalData.current_profit.toFixed(2)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{goalData.progress_percent.toFixed(1)}%</div>
              <Badge className={`mt-1 ${pace.color}`}>{pace.label}</Badge>
            </CardContent>
          </Card>
        </div>

        {/* Progress Bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-xs text-gray-500">
              {goalData.current_calls} / {goalData.calls_needed} calls
            </span>
          </div>
          <Progress value={Math.min(goalData.progress_percent, 100)} className="h-2" />
        </div>

        {/* Calls and Reservations */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Calls Needed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{goalData.calls_needed}</div>
              <p className="text-xs text-gray-500 mt-1">
                Completed: {goalData.current_calls}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Reservations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{goalData.reservations_needed}</div>
              <p className="text-xs text-gray-500 mt-1">
                Completed: {goalData.current_reservations}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Time Remaining */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Time Remaining
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatTime(goalData.time_remaining_minutes)}</div>
            <p className="text-xs text-gray-500 mt-1">
              Total needed: {formatTime(goalData.time_needed_minutes)}
            </p>
          </CardContent>
        </Card>

        {/* Metrics Summary */}
        <Card className="bg-gray-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Booking Speed:</span>
              <span className="font-medium">1 booking / 30 min</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Conversion Rate:</span>
              <span className="font-medium">16%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Avg Profit/Booking:</span>
              <span className="font-medium">$2.40</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Goals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500">Loading goals...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Error loading goals: {error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Goals</CardTitle>
        <CardDescription>
          Track your progress toward daily, weekly, and biweekly targets
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="daily">Daily</TabsTrigger>
            <TabsTrigger value="weekly">Weekly</TabsTrigger>
            <TabsTrigger value="biweekly">Biweekly</TabsTrigger>
          </TabsList>

          <TabsContent value="daily" className="mt-6">
            {renderGoalCard('Daily', goals?.daily)}
          </TabsContent>

          <TabsContent value="weekly" className="mt-6">
            {renderGoalCard('Weekly', goals?.weekly)}
          </TabsContent>

          <TabsContent value="biweekly" className="mt-6">
            {renderGoalCard('Biweekly', goals?.biweekly)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

export default GoalDisplay;
