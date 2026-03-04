import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';

/**
 * Booking Delete Confirmation Dialog
 * 
 * Bug Fix #7: Booking Deletion - No Confirmation
 * Shows confirmation dialog before deleting a booking
 */
function BookingDeleteDialog({ 
  isOpen, 
  onClose, 
  onConfirm, 
  booking,
  isDeleting 
}) {
  if (!booking) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Booking</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this booking? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="bg-zinc-50 dark:bg-zinc-900 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-zinc-500">Profit:</span>
              <span className="font-medium">${booking.profit?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Type:</span>
              <span className="font-medium">
                {booking.is_prepaid ? 'Prepaid' : 'Regular'}
                {booking.has_refund_protection && ' + Refund Protection'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Date:</span>
              <span className="font-medium">
                {booking.timestamp 
                  ? new Date(booking.timestamp).toLocaleDateString() 
                  : 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        <DialogFooter className="sm:justify-end">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Booking'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default BookingDeleteDialog;