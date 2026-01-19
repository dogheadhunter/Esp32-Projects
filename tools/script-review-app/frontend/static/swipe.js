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
        this.isScrolling = false;
        // Responsive threshold: 35% of screen width, max 200px
        this.threshold = Math.min(200, window.innerWidth * 0.35);
        this.scrollThreshold = 15; // If vertical movement exceeds this, treat as scroll
        
        this.init();
    }
    
    init() {
        // Touch events
        this.element.addEventListener('touchstart', this.handleStart.bind(this), { passive: true });
        this.element.addEventListener('touchmove', this.handleMove.bind(this), { passive: false });
        this.element.addEventListener('touchend', this.handleEnd.bind(this));
        
        // Mouse events for desktop testing
        this.element.addEventListener('mousedown', this.handleStart.bind(this));
        this.element.addEventListener('mousemove', this.handleMove.bind(this));
        this.element.addEventListener('mouseup', this.handleEnd.bind(this));
        this.element.addEventListener('mouseleave', this.handleEnd.bind(this));
    }
    
    handleStart(e) {
        // Reset state
        this.isDragging = false;
        this.isScrolling = false;
        this.intentDetermined = false;
        
        if (e.type === 'mousedown') {
            this.startX = e.clientX;
            this.startY = e.clientY;
        } else {
            this.startX = e.touches[0].clientX;
            this.startY = e.touches[0].clientY;
        }
        
        // Store the target to check if it's scrollable area
        this.startTarget = e.target || e.touches?.[0]?.target;
    }
    
    handleMove(e) {
        if (this.isScrolling) return;
        
        if (e.type === 'mousemove') {
            this.currentX = e.clientX;
            this.currentY = e.clientY;
        } else if (e.touches && e.touches.length > 0) {
            this.currentX = e.touches[0].clientX;
            this.currentY = e.touches[0].clientY;
        } else {
            return;
        }
        
        const diffX = this.currentX - this.startX;
        const diffY = this.currentY - this.startY;
        
        // Determine intent on first significant movement
        if (!this.intentDetermined && (Math.abs(diffX) > this.scrollThreshold || Math.abs(diffY) > this.scrollThreshold)) {
            this.intentDetermined = true;
            
            // Check if target is in scrollable area
            const scrollableArea = this.startTarget?.closest('.overflow-y-auto') || this.startTarget?.closest('.scrollable-content');
            
            // If vertical movement is dominant AND in scrollable area, this is a scroll
            if (Math.abs(diffY) > Math.abs(diffX) && scrollableArea) {
                this.isScrolling = true;
                return;
            }
            
            // If horizontal movement is dominant, this is a swipe
            if (Math.abs(diffX) > Math.abs(diffY)) {
                this.isDragging = true;
                this.element.classList.add('swiping');
            }
        }
        
        // Only proceed if we've determined this is a swipe
        if (!this.isDragging) return;
        
        // Prevent default scroll only for confirmed swipe
        e.preventDefault();
        
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
        if (this.isScrolling) {
            this.isDragging = false;
            this.isScrolling = false;
            this.intentDetermined = false;
            return;
        }
        
        if (!this.isDragging) {
            this.intentDetermined = false;
            return;
        }
        
        this.isDragging = false;
        this.intentDetermined = false;
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
