// Initialize Lucide Icons
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
});

// Re-init icons after HTMX swaps
document.body.addEventListener('htmx:afterSwap', () => {
    lucide.createIcons();
});

// Alpine.js Data
function appData() {
    return {
        historyOpen: false,
        toggleHistory() {
            this.historyOpen = !this.historyOpen;
        },
        deleteModalOpen: false,
        toggleDeleteModal() {
            this.deleteModalOpen = !this.deleteModalOpen;
        },
        // Toast Notification Logic
        showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';

            const iconName = type === 'success' ? 'check-circle' : 'alert-circle';
            const iconColor = type === 'success' ? 'text-green-500' : 'text-red-500';

            toast.innerHTML = `
                <i data-lucide="${iconName}" class="w-5 h-5 ${iconColor}"></i>
                <span>${message}</span>
            `;

            container.appendChild(toast);
            lucide.createIcons();

            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-20px)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    }
}
