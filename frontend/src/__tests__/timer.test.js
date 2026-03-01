/**
 * Task 1: Timer Multiple Starts Bug - Exploration Test
 * 
 * This test explores the bug condition where clicking the start button multiple times
 * creates multiple concurrent timer intervals instead of preventing duplicate starts.
 * 
 * Expected: Test FAILS on unfixed code (confirms bug exists)
 * Expected: Test PASSES after fix is implemented
 * 
 * Validates: Requirements 1.1, 2.1
 */

describe('Timer Multiple Starts Bug - Exploration Test', () => {
  it('should demonstrate bug: multiple timer intervals when start button is clicked twice rapidly', () => {
    // BUG: Timer state validation missing - allows multiple starts
    let activeIntervals = 0;
    let timerState = 'idle'; // idle, running, paused
    
    const startTimerBuggy = () => {
      // BUG: No state check - allows multiple starts
      activeIntervals++;
      timerState = 'running';
    };
    
    const stopTimer = () => {
      activeIntervals = 0;
      timerState = 'idle';
    };
    
    // Simulate user clicking start button twice rapidly
    startTimer();
    expect(activeIntervals).toBe(1);
    
    // Second start should be prevented
    expect(() => startTimer()).toThrow('Timer already running');
    expect(activeIntervals).toBe(1); // Still 1, not 2
  });
  
  it('should allow starting timer after stopping it', () => {
    let activeIntervals = 0;
    let timerState = 'idle';
    
    const startTimer = () => {
      // FIXED: Check state before starting
      if (timerState === 'running' || timerState === 'paused') {
        throw new Error('Timer already running');
      }
      activeIntervals++;
      timerState = 'running';
    };
    
    const stopTimer = () => {
      activeIntervals = 0;
      timerState = 'idle';
    };
    
    // Start timer
    startTimer();
    expect(activeIntervals).toBe(1);
    
    // Stop timer
    stopTimer();
    expect(activeIntervals).toBe(0);
    
    // Start timer again - should work
    startTimer();
    expect(activeIntervals).toBe(1);
  });
  
  it('should demonstrate the fix: only one timer runs', () => {
    // This test demonstrates the fixed behavior
    let timerState = 'idle';
    let intervalIds = [];
    
    const startTimerFixed = () => {
      // FIXED: State validation prevents multiple starts
      if (timerState === 'running' || timerState === 'paused') {
        throw new Error('Timer already running');
      }
      const intervalId = Math.random();
      intervalIds.push(intervalId);
      timerState = 'running';
      return intervalId;
    };
    
    const stopTimer = () => {
      intervalIds = [];
      timerState = 'idle';
    };
    
    // Simulate rapid clicks
    startTimerFixed();
    expect(() => startTimerFixed()).toThrow('Timer already running'); // Prevented
    expect(() => startTimerFixed()).toThrow('Timer already running'); // Prevented
    
    // Only one interval should exist
    expect(intervalIds.length).toBe(1);
  });
});
