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
    profit_daily: 72.08,
    profit_weekly: 504.56,
    profit_biweekly: 1009.12,
    spins_daily: 18.00,
    spins_weekly: 126.00,
    spins_biweekly: 252.00,
    reservations_daily: 16,
    reservations_weekly: 112,
    reservations_biweekly: 224,
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
          profit_daily: data.profit_daily || 72.08,
          profit_weekly: data.profit_weekly || 504.56,
          profit_biweekly: data.profit_biweekly || 1009.12,
          spins_daily: data.spins_daily || 18.00,
          spins_weekly: data.spins_weekly || 126.00,
          spins_biweekly: data.spins_biweekly || 252.00,
          reservations_daily: data.reservations_daily || 16,
          reservations_weekly: data.reservations_weekly || 112,
          reservations_biweekly: data.reservations_biweekly || 224,
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
    const profitDaily = 72.08;
    const profitWeekly = profitDaily * 5; // 5 working days
    const profitBiweekly = profitWeekly * 2; // 2 weeks
    
    // Spins: $18/day fixed
    const spinsDaily = 18.00;
    const spinsWeekly = spinsDaily * 7;
    const spinsBiweekly = spinsWeekly * 2;
    
    // Reservations: 16/day
    const reservationsDaily = 16;
    const reservationsWeekly = reservationsDaily * 7;
    const reservationsBiweekly = reservationsWeekly * 2;

    setTargets({
      profit_daily: parseFloat(profitDaily.toFixed(2)),
      profit_weekly: parseFloat(profitWeekly.toFixed(2)),
      profit_biweekly: parseFloat(profitBiweekly.toFixed(2)),
      spins_daily: parseFloat(spinsDaily.toFixed(2)),
      spins_weekly: parseFloat(spinsWeekly.toFixed(2)),
      spins_biweekly: parseFloat(spinsBiweekly.toFixed(2)),
      reservations_daily: reservationsDaily,
      reservations_weekly: reservationsWeekly,
      reservations_biweekly: reservationsBiweekly,
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
          profit_daily: targets.profit_daily,
          profit_weekly: targets.profit_weekly,
          profit_biweekly: targets.profit_biweekly,
          spins_daily: targets.spins_daily,
          spins_weekly: targets.spins_weekly,
          spins_biweekly: targets.spins_biweekly,
          reservations_daily: targets.reservations_daily,
          reservations_weekly: targets.reservations_weekly,
          reservations_biweekly: targets.reservations_biweekly,
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
      profit_daily: 72.08,
      profit_weekly: 504.56,
      profit_biweekly: 1009.12,
      spins_daily: 18.00,
      spins_weekly: 126.00,
      spins_biweekly: 252.00,
      reservations_daily: 16,
      reservations_weekly: 112,
      reservations_biweekly: 224,
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
              All targets updated successfully! Goals will be recalculated at the next period boundary.
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

        <div className="space-y-6">
          {/* PROFIT TARGETS */}
          <div className="border-b pb-4">
            <h3 className="font-semibold text-base mb-4">Profit Targets</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="profit_daily" className="text-base font-medium">
                  Daily Profit Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="profit_daily"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.profit_daily}
                    onChange={(e) => handleInputChange('profit_daily', e.target.value)}
                    placeholder="Enter daily target"
                    className="flex-1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="profit_weekly" className="text-base font-medium">
                  Weekly Profit Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="profit_weekly"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.profit_weekly}
                    onChange={(e) => handleInputChange('profit_weekly', e.target.value)}
                    placeholder="Enter weekly target"
                    className="flex-1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="profit_biweekly" className="text-base font-medium">
                  Biweekly Profit Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="profit_biweekly"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.profit_biweekly}
                    onChange={(e) => handleInputChange('profit_biweekly', e.target.value)}
                    placeholder="Enter biweekly target"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* SPINS TARGETS */}
          <div className="border-b pb-4">
            <h3 className="font-semibold text-base mb-4">Spins Targets</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="spins_daily" className="text-base font-medium">
                  Daily Spins Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="spins_daily"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.spins_daily}
                    onChange={(e) => handleInputChange('spins_daily', e.target.value)}
                    placeholder="Enter daily target"
                    className="flex-1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="spins_weekly" className="text-base font-medium">
                  Weekly Spins Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="spins_weekly"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.spins_weekly}
                    onChange={(e) => handleInputChange('spins_weekly', e.target.value)}
                    placeholder="Enter weekly target"
                    className="flex-1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="spins_biweekly" className="text-base font-medium">
                  Biweekly Spins Target
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">$</span>
                  <Input
                    id="spins_biweekly"
                    type="number"
                    step="0.01"
                    min="0"
                    value={targets.spins_biweekly}
                    onChange={(e) => handleInputChange('spins_biweekly', e.target.value)}
                    placeholder="Enter biweekly target"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* RESERVATIONS TARGETS */}
          <div className="border-b pb-4">
            <h3 className="font-semibold text-base mb-4">Reservations Targets</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="reservations_daily" className="text-base font-medium">
                  Daily Reservations Target
                </Label>
                <Input
                  id="reservations_daily"
                  type="number"
                  step="1"
                  min="0"
                  value={targets.reservations_daily}
                  onChange={(e) => handleInputChange('reservations_daily', e.target.value)}
                  placeholder="Enter daily target"
                  className="flex-1"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reservations_weekly" className="text-base font-medium">
                  Weekly Reservations Target
                </Label>
                <Input
                  id="reservations_weekly"
                  type="number"
                  step="1"
                  min="0"
                  value={targets.reservations_weekly}
                  onChange={(e) => handleInputChange('reservations_weekly', e.target.value)}
                  placeholder="Enter weekly target"
                  className="flex-1"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reservations_biweekly" className="text-base font-medium">
                  Biweekly Reservations Target
                </Label>
                <Input
                  id="reservations_biweekly"
                  type="number"
                  step="1"
                  min="0"
                  value={targets.reservations_biweekly}
                  onChange={(e) => handleInputChange('reservations_biweekly', e.target.value)}
                  placeholder="Enter biweekly target"
                  className="flex-1"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Summary */}
        <Card className="bg-gray-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Target Summary</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-3">
            <div>
              <div className="font-semibold text-gray-700 mb-2">Profit</div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Daily:</span>
                <span className="font-medium">${targets.profit_daily.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Weekly:</span>
                <span className="font-medium">${targets.profit_weekly.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Biweekly:</span>
                <span className="font-medium">${targets.profit_biweekly.toFixed(2)}</span>
              </div>
            </div>
            <div className="border-t pt-2">
              <div className="font-semibold text-gray-700 mb-2">Spins</div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Daily:</span>
                <span className="font-medium">${targets.spins_daily.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Weekly:</span>
                <span className="font-medium">${targets.spins_weekly.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Biweekly:</span>
                <span className="font-medium">${targets.spins_biweekly.toFixed(2)}</span>
              </div>
            </div>
            <div className="border-t pt-2">
              <div className="font-semibold text-gray-700 mb-2">Reservations</div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Daily:</span>
                <span className="font-medium">{targets.reservations_daily}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Weekly:</span>
                <span className="font-medium">{targets.reservations_weekly}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Biweekly:</span>
                <span className="font-medium">{targets.reservations_biweekly}</span>
              </div>
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
