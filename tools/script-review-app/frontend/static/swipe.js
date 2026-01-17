/**
 * Swipe Gesture Handler
 */

class SwipeHandler {
    constructor(element, callbacks) {
        this.element = element;
        this.callbacks = callbacks;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.isDragging = false;
        this.threshold = 100; // pixels to trigger swipe
        
        this.init();
    }
    
    init() {
        // Touch events
        this.element.addEventListener('touchstart', this.handleStart.bind(this));
        this.element.addEventListener('touchmove', this.handleMove.bind(this));
        this.element.addEventListener('touchend', this.handleEnd.bind(this));
        
        // Mouse events for desktop testing
        this.element.addEventListener('mousedown', this.handleStart.bind(this));
        this.element.addEventListener('mousemove', this.handleMove.bind(this));
        this.element.addEventListener('mouseup', this.handleEnd.bind(this));
        this.element.addEventListener('mouseleave', this.handleEnd.bind(this));
    }
    
    handleStart(e) {
        if (e.type === 'mousedown') {
            this.startX = e.clientX;
            this.startY = e.clientY;
        } else {
            this.startX = e.touches[0].clientX;
            this.startY = e.touches[0].clientY;
        }
        
        this.isDragging = true;
        this.element.classList.add('swiping');
    }
    
    handleMove(e) {
        if (!this.isDragging) return;
        
        e.preventDefault();
        
        if (e.type === 'mousemove') {
            this.currentX = e.clientX;
            this.currentY = e.clientY;
        } else {
            this.currentX = e.touches[0].clientX;
            this.currentY = e.touches[0].clientY;
        }
        
        const diffX = this.currentX - this.startX;
        const diffY = this.currentY - this.startY;
        const rotation = diffX / 10;
        
        // Apply transform
        this.element.style.transform = `translateX(${diffX}px) rotate(${rotation}deg)`;
        
        // Show approve/reject indicators
        const approveIndicator = this.element.querySelector('.approve-indicator');
        const rejectIndicator = this.element.querySelector('.reject-indicator');
        
        if (diffX > 50) {
            approveIndicator.style.opacity = Math.min(diffX / this.threshold, 1);
            rejectIndicator.style.opacity = 0;
        } else if (diffX < -50) {
            rejectIndicator.style.opacity = Math.min(Math.abs(diffX) / this.threshold, 1);
            approveIndicator.style.opacity = 0;
        } else {
            approveIndicator.style.opacity = 0;
            rejectIndicator.style.opacity = 0;
        }
    }
    
    handleEnd(e) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.element.classList.remove('swiping');
        
        const diffX = this.currentX - this.startX;
        
        // Reset indicators
        const approveIndicator = this.element.querySelector('.approve-indicator');
        const rejectIndicator = this.element.querySelector('.reject-indicator');
        approveIndicator.style.opacity = 0;
        rejectIndicator.style.opacity = 0;
        
        if (Math.abs(diffX) > this.threshold) {
            // Swipe threshold met
            if (diffX > 0) {
                this.callbacks.onApprove && this.callbacks.onApprove();
            } else {
                this.callbacks.onReject && this.callbacks.onReject();
            }
        } else {
            // Snap back
            this.element.style.transform = '';
        }
    }
    
    destroy() {
        this.element.removeEventListener('touchstart', this.handleStart);
        this.element.removeEventListener('touchmove', this.handleMove);
        this.element.removeEventListener('touchend', this.handleEnd);
        this.element.removeEventListener('mousedown', this.handleStart);
        this.element.removeEventListener('mousemove', this.handleMove);
        this.element.removeEventListener('mouseup', this.handleEnd);
        this.element.removeEventListener('mouseleave', this.handleEnd);
    }
}
