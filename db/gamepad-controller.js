// PS4 DualShock 4 Controller Support
// Handles gamepad input for navigation and interaction

class GamepadController {
    constructor() {
        this.gamepad = null;
        this.previousButtons = {};
        this.axisThreshold = 0.5;
        this.scrollSpeed = 30;
        this.focusedElement = null;
        this.focusableElements = [];
        this.currentFocusIndex = 0;
        this.isActive = false;
        
        // Button mapping for DualShock 4
        this.buttons = {
            X: 0,           // Cross (Confirm/Select)
            CIRCLE: 1,      // Circle (Back/Cancel)
            SQUARE: 2,      // Square (Options)
            TRIANGLE: 3,    // Triangle (Search)
            L1: 4,
            R1: 5,
            L2: 6,
            R2: 7,
            SHARE: 8,
            OPTIONS: 9,
            L3: 10,
            R3: 11,
            DPAD_UP: 12,
            DPAD_DOWN: 13,
            DPAD_LEFT: 14,
            DPAD_RIGHT: 15,
            PS: 16
        };
        
        // Axis mapping
        this.axes = {
            LEFT_STICK_X: 0,
            LEFT_STICK_Y: 1,
            RIGHT_STICK_X: 2,
            RIGHT_STICK_Y: 3
        };
        
        this.init();
    }
    
    init() {
        // Listen for gamepad connection
        window.addEventListener('gamepadconnected', (e) => {
            console.log('Gamepad connected:', e.gamepad.id);
            this.gamepad = e.gamepad;
            this.isActive = true;
            this.showControllerHints();
            this.updateFocusableElements();
            this.startPolling();
        });
        
        window.addEventListener('gamepaddisconnected', (e) => {
            console.log('Gamepad disconnected');
            this.gamepad = null;
            this.isActive = false;
            this.hideControllerHints();
            this.stopPolling();
        });
        
        // Check for already connected gamepads
        this.checkGamepads();
    }
    
    checkGamepads() {
        const gamepads = navigator.getGamepads();
        for (let i = 0; i < gamepads.length; i++) {
            if (gamepads[i]) {
                this.gamepad = gamepads[i];
                this.isActive = true;
                this.showControllerHints();
                this.updateFocusableElements();
                this.startPolling();
                break;
            }
        }
    }
    
    startPolling() {
        if (this.pollingInterval) return;
        
        this.pollingInterval = setInterval(() => {
            this.poll();
        }, 16); // ~60 FPS
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    poll() {
        if (!this.isActive) return;
        
        // Get latest gamepad state
        const gamepads = navigator.getGamepads();
        this.gamepad = gamepads[0]; // Assume first gamepad
        
        if (!this.gamepad) return;
        
        this.handleButtons();
        this.handleAxes();
    }
    
    handleButtons() {
        const buttons = this.gamepad.buttons;
        
        // X Button - Confirm/Select
        if (this.isButtonPressed(this.buttons.X)) {
            this.onXButton();
        }
        
        // Circle Button - Back/Cancel
        if (this.isButtonPressed(this.buttons.CIRCLE)) {
            this.onCircleButton();
        }
        
        // Triangle Button - Search
        if (this.isButtonPressed(this.buttons.TRIANGLE)) {
            this.onTriangleButton();
        }
        
        // Square Button - Options
        if (this.isButtonPressed(this.buttons.SQUARE)) {
            this.onSquareButton();
        }
        
        // D-Pad Navigation
        if (this.isButtonPressed(this.buttons.DPAD_UP)) {
            this.navigateUp();
        }
        if (this.isButtonPressed(this.buttons.DPAD_DOWN)) {
            this.navigateDown();
        }
        if (this.isButtonPressed(this.buttons.DPAD_LEFT)) {
            this.navigateLeft();
        }
        if (this.isButtonPressed(this.buttons.DPAD_RIGHT)) {
            this.navigateRight();
        }
        
        // L1/R1 - Page navigation
        if (this.isButtonPressed(this.buttons.L1)) {
            this.pageUp();
        }
        if (this.isButtonPressed(this.buttons.R1)) {
            this.pageDown();
        }
    }
    
    handleAxes() {
        const axes = this.gamepad.axes;
        
        // Left stick - Navigation
        const leftX = axes[this.axes.LEFT_STICK_X];
        const leftY = axes[this.axes.LEFT_STICK_Y];
        
        if (Math.abs(leftY) > this.axisThreshold) {
            if (leftY < -this.axisThreshold) {
                this.scrollUp();
            } else if (leftY > this.axisThreshold) {
                this.scrollDown();
            }
        }
        
        if (Math.abs(leftX) > this.axisThreshold) {
            if (leftX < -this.axisThreshold) {
                this.navigateLeft();
            } else if (leftX > this.axisThreshold) {
                this.navigateRight();
            }
        }
    }
    
    isButtonPressed(buttonIndex) {
        const button = this.gamepad.buttons[buttonIndex];
        const isPressed = button.pressed;
        const wasPressed = this.previousButtons[buttonIndex];
        
        this.previousButtons[buttonIndex] = isPressed;
        
        // Return true only on button press (not hold)
        return isPressed && !wasPressed;
    }
    
    // Button Actions
    onXButton() {
        console.log('X Button pressed - Confirm/Select');
        if (this.focusedElement) {
            this.focusedElement.click();
        }
    }
    
    onCircleButton() {
        console.log('Circle Button pressed - Back/Cancel');
        // Close search if open
        const searchBox = document.getElementById('searchBox');
        if (searchBox && searchBox === document.activeElement) {
            searchBox.blur();
            return;
        }
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    onTriangleButton() {
        console.log('Triangle Button pressed - Search');
        const searchBox = document.getElementById('searchBox');
        if (searchBox) {
            searchBox.focus();
        }
    }
    
    onSquareButton() {
        console.log('Square Button pressed - Options');
        // Toggle view mode or show help
        this.toggleViewMode();
    }
    
    // Navigation
    navigateUp() {
        this.moveFocus(-1);
    }
    
    navigateDown() {
        this.moveFocus(1);
    }
    
    navigateLeft() {
        // Navigate to previous letter section
        this.navigateSection(-1);
    }
    
    navigateRight() {
        // Navigate to next letter section
        this.navigateSection(1);
    }
    
    scrollUp() {
        window.scrollBy({ top: -this.scrollSpeed, behavior: 'auto' });
    }
    
    scrollDown() {
        window.scrollBy({ top: this.scrollSpeed, behavior: 'auto' });
    }
    
    pageUp() {
        window.scrollBy({ top: -window.innerHeight * 0.8, behavior: 'smooth' });
    }
    
    pageDown() {
        window.scrollBy({ top: window.innerHeight * 0.8, behavior: 'smooth' });
    }
    
    updateFocusableElements() {
        this.focusableElements = Array.from(document.querySelectorAll(
            'button, a, input, [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
            return el.offsetParent !== null; // Only visible elements
        });
    }
    
    moveFocus(direction) {
        this.updateFocusableElements();
        
        if (this.focusableElements.length === 0) return;
        
        this.currentFocusIndex += direction;
        
        if (this.currentFocusIndex < 0) {
            this.currentFocusIndex = this.focusableElements.length - 1;
        } else if (this.currentFocusIndex >= this.focusableElements.length) {
            this.currentFocusIndex = 0;
        }
        
        this.focusedElement = this.focusableElements[this.currentFocusIndex];
        this.focusedElement.focus();
        this.focusedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    navigateSection(direction) {
        const sections = document.querySelectorAll('.letter-section');
        if (sections.length === 0) return;
        
        const currentScroll = window.scrollY;
        let targetSection = null;
        
        if (direction > 0) {
            // Find next section
            for (let section of sections) {
                if (section.offsetTop > currentScroll + 100) {
                    targetSection = section;
                    break;
                }
            }
        } else {
            // Find previous section
            for (let i = sections.length - 1; i >= 0; i--) {
                if (sections[i].offsetTop < currentScroll - 100) {
                    targetSection = sections[i];
                    break;
                }
            }
        }
        
        if (targetSection) {
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    toggleViewMode() {
        // Toggle between compact and detailed view
        const gamesList = document.getElementById('gamesList');
        if (gamesList) {
            gamesList.classList.toggle('compact-view');
        }
    }
    
    showControllerHints() {
        const hints = document.getElementById('controllerHints');
        if (hints) {
            hints.style.display = 'block';
        }
    }
    
    hideControllerHints() {
        const hints = document.getElementById('controllerHints');
        if (hints) {
            hints.style.display = 'none';
        }
    }
}

// Initialize controller when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.gamepadController = new GamepadController();
    });
} else {
    window.gamepadController = new GamepadController();
}
