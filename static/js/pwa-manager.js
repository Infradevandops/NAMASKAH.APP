/**
 * PWA Manager - Handles PWA installation, offline detection, and service worker updates
 */
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
        this.installButton = null;
        this.offlineIndicator = null;
        this.updateNotification = null;

        this.init();
    }

    init() {
        // Register service worker
        this.registerServiceWorker();

        // Set up event listeners
        this.setupEventListeners();

        // Create UI elements
        this.createInstallButton();
        this.createOfflineIndicator();
        this.createUpdateNotification();

        // Check for updates
        this.checkForUpdates();
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/service-worker.js')
                    .then(registration => {
                        console.log('PWA: Service Worker registered successfully:', registration);

                        // Listen for updates
                        registration.addEventListener('updatefound', () => {
                            const newWorker = registration.installing;
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    this.showUpdateNotification();
                                }
                            });
                        });

                        // Handle messages from service worker
                        navigator.serviceWorker.addEventListener('message', event => {
                            this.handleServiceWorkerMessage(event.data);
                        });
                    })
                    .catch(error => {
                        console.error('PWA: Service Worker registration failed:', error);
                    });
            });
        }
    }

    setupEventListeners() {
        // Listen for install prompt
        window.addEventListener('beforeinstallprompt', event => {
            console.log('PWA: beforeinstallprompt fired');
            event.preventDefault();
            this.deferredPrompt = event;
            this.showInstallButton();
        });

        // Listen for app installation
        window.addEventListener('appinstalled', event => {
            console.log('PWA: App installed successfully');
            this.hideInstallButton();
            this.deferredPrompt = null;
        });

        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('PWA: Back online');
            this.isOnline = true;
            this.hideOfflineIndicator();
            this.syncWhenOnline();
        });

        window.addEventListener('offline', () => {
            console.log('PWA: Gone offline');
            this.isOnline = false;
            this.showOfflineIndicator();
        });
    }

    createInstallButton() {
        this.installButton = document.createElement('button');
        this.installButton.id = 'pwa-install-button';
        this.installButton.className = 'btn btn-primary position-fixed';
        this.installButton.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        this.installButton.innerHTML = '<i class="fas fa-download"></i>';
        this.installButton.title = 'Install namaskah';
        this.installButton.setAttribute('aria-label', 'Install namaskah as an app');

        this.installButton.addEventListener('click', () => {
            this.installPWA();
        });

        document.body.appendChild(this.installButton);
    }

    createOfflineIndicator() {
        this.offlineIndicator = document.createElement('div');
        this.offlineIndicator.id = 'offline-indicator';
        this.offlineIndicator.className = 'alert alert-warning position-fixed';
        this.offlineIndicator.style.cssText = `
            top: 0;
            left: 0;
            right: 0;
            z-index: 999;
            border-radius: 0;
            text-align: center;
            display: none;
            margin: 0;
        `;
        this.offlineIndicator.innerHTML = `
            <i class="fas fa-wifi-slash me-2"></i>
            You're offline. Some features may be limited.
            <button type="button" class="btn btn-sm btn-outline-dark ms-3" onclick="location.reload()">
                <i class="fas fa-sync-alt"></i> Retry
            </button>
        `;

        document.body.appendChild(this.offlineIndicator);
    }

    createUpdateNotification() {
        this.updateNotification = document.createElement('div');
        this.updateNotification.id = 'update-notification';
        this.updateNotification.className = 'alert alert-info position-fixed';
        this.updateNotification.style.cssText = `
            bottom: 100px;
            right: 20px;
            z-index: 1000;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: none;
            max-width: 300px;
        `;
        this.updateNotification.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">
                    <strong>Update Available</strong><br>
                    <small>A new version of namaskah is ready to install.</small>
                </div>
                <div class="ms-2">
                    <button class="btn btn-sm btn-primary me-1" onclick="pwaManager.updateApp()">
                        <i class="fas fa-download"></i> Update
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="pwaManager.dismissUpdate()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.updateNotification);
    }

    showInstallButton() {
        if (this.installButton && !window.matchMedia('(display-mode: standalone)').matches) {
            this.installButton.style.display = 'flex';
            this.installButton.style.alignItems = 'center';
            this.installButton.style.justifyContent = 'center';
        }
    }

    hideInstallButton() {
        if (this.installButton) {
            this.installButton.style.display = 'none';
        }
    }

    showOfflineIndicator() {
        if (this.offlineIndicator) {
            this.offlineIndicator.style.display = 'block';
        }
    }

    hideOfflineIndicator() {
        if (this.offlineIndicator) {
            this.offlineIndicator.style.display = 'none';
        }
    }

    showUpdateNotification() {
        if (this.updateNotification) {
            this.updateNotification.style.display = 'block';
        }
    }

    hideUpdateNotification() {
        if (this.updateNotification) {
            this.updateNotification.style.display = 'none';
        }
    }

    async installPWA() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;

            if (outcome === 'accepted') {
                console.log('PWA: User accepted the install prompt');
            } else {
                console.log('PWA: User dismissed the install prompt');
            }

            this.deferredPrompt = null;
            this.hideInstallButton();
        }
    }

    updateApp() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistration().then(registration => {
                if (registration && registration.waiting) {
                    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                    window.location.reload();
                }
            });
        }
        this.hideUpdateNotification();
    }

    dismissUpdate() {
        this.hideUpdateNotification();
    }

    checkForUpdates() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistration().then(registration => {
                if (registration) {
                    registration.update();
                }
            });
        }
    }

    async syncWhenOnline() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('background-sync-messages');
                console.log('PWA: Background sync registered');
            } catch (error) {
                console.error('PWA: Background sync registration failed:', error);
            }
        }
    }

    handleServiceWorkerMessage(data) {
        if (data && data.type === 'UPDATE_AVAILABLE') {
            this.showUpdateNotification();
        }
    }

    // Utility methods
    isInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    getConnectionStatus() {
        return {
            online: this.isOnline,
            installed: this.isInstalled(),
            canInstall: !!this.deferredPrompt
        };
    }
}

// Create global instance
window.pwaManager = new PWAManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}