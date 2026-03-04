import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';

/**
 * GoalSetter Component
 * Allows users to set profit targets for daily, weekly, and biweekly periods
 */
export function GoalSetter({ userId, onTargetsUpdated }) {
  const [targets, setTargets] = useState({
    daily_target: 72.08,
    weekly_target: 504.56,
    biweekly_target: 1009.12,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [autoCalculate, setAutoCalculate] = useState(false);

  useEffect(() => {
    fetchCurrentTargets();
  }, [userId]);

  const fetchCurrentTargets = async () => {
    try {
      const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/goals`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTargets({
          daily_target: data.profit_daily || 72.08,
          weekly_target: data.profit_weekly || 504.56,
          biweekly_target: data.profit_biweekly || 1009.12,
        });
      }
    } catch (err) {
      console.error('Error fetching targets:', err);
    }
  };

  const handleInputChange = (field, value) => {
    const numValue = parseFloat(value) || 0;
    setTargets(prev => ({
      ...prev,
      [field]: numValue
    }));
    setSuccess(false);
  };

  const handleAutoCalculate = () => {
    // Auto-calculate based on working days
    // Assuming 5 working days per week, 8 hours per day
    const dailyTarget = 72.08;
    const weeklyTarget = dailyTarget * 5; // 5 working days
    const biweeklyTarget = weeklyTarget * 2; // 2 weeks

    setTargets({
      daily_target: parseFloat(dailyTarget.toFixed(2)),
      weekly_target: parseFloat(weeklyTarget.toFixed(2)),
      biweekly_target: parseFloat(biweeklyTarget.toFixed(2)),
    });
    setAutoCalculate(true);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/goals`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          profit_daily: targets.daily_target,
          profit_weekly: targets.weekly_target,
          profit_biweekly: targets.biweekly_target
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save targets');
      }

      setSuccess(true);
      if (onTargetsUpdated) {
        onTargetsUpdated(targets);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
      console.error('Error saving targets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setTargets({
      daily_target: 72.08,
      weekly_target: 504.56,
      biweekly_target: 1009.12,
    });
    setAutoCalculate(false);
    setSuccess(false);
    setError(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Set Profit Targets</CardTitle>
        <CardDescription>
          Define your profit targets for each period. Goals will be automatically calculated based on these targets.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Profit targets updated successfully! Goals will be recalculated at the next period boundary.
            </AlertDescription>
          </Alert>
        )}

        {autoCalculate && (
          <Alert className="bg-blue-50 border-blue-200">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              Auto-calculated based on 5 working days per week
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {/* Daily Target */}
          <div className="space-y-2">
            <Label htmlFor="daily_target" className="text-base font-medium">
              Daily Profit Target
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">$</span>
              <Input
                id="daily_target"
                type="number"
                step="0.01"
                min="0"
                value={targets.daily_target}
                onChange={(e) => handleInputChange('daily_target', e.target.value)}
                placeholder="Enter daily target"
                className="flex-1"
              />
            </div>
            <p className="text-xs text-gray-500">
              Target profit to earn each day
            </p>
          </div>

          {/* Weekly Target */}
          <div className="space-y-2">
            <Label htmlFor="weekly_target" className="text-base font-medium">
              Weekly Profit Target
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">$</span>
              <Input
                id="weekly_target"
                type="number"
                step="0.01"
                min="0"
                value={targets.weekly_target}
                onChange={(e) => handleInputChange('weekly_target', e.target.value)}
                placeholder="Enter weekly target"
                className="flex-1"
              />
            </div>
            <p className="text-xs text-gray-500">
              Target profit to earn each week (Sunday-Saturday)
            </p>
          </div>

          {/* Biweekly Target */}
          <div className="space-y-2">
            <Label htmlFor="biweekly_target" className="text-base font-medium">
              Biweekly Profit Target
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">$</span>
              <Input
                id="biweekly_target"
                type="number"
                step="0.01"
                min="0"
                value={targets.biweekly_target}
                onChange={(e) => handleInputChange('biweekly_target', e.target.value)}
                placeholder="Enter biweekly target"
                className="flex-1"
              />
            </div>
            <p className="text-xs text-gray-500">
              Target profit to earn every two weeks (1st-15th and 16th-end of month)
            </p>
          </div>
        </div>

        {/* Summary */}
        <Card className="bg-gray-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Target Summary</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Daily:</span>
              <span className="font-medium">${targets.daily_target.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Weekly:</span>
              <span className="font-medium">${targets.weekly_target.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Biweekly:</span>
              <span className="font-medium">${targets.biweekly_target.toFixed(2)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button
            onClick={handleSave}
            disabled={loading}
            className="flex-1"
          >
            {loading ? (
              <>
                <Loader className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Targets'
            )}
          </Button>
          <Button
            onClick={handleAutoCalculate}
            variant="outline"
            className="flex-1"
          >
            Auto-Calculate
          </Button>
          <Button
            onClick={handleReset}
            variant="ghost"
          >
            Reset
          </Button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          Goals are recalculated at period boundaries (daily at 12 AM, weekly on Saturday, biweekly on 1st and 16th)
        </p>
      </CardContent>
    </Card>
  );
}

export default GoalSetter;
