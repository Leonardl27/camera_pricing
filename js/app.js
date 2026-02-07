// Camera Pricing Dashboard App

class CameraDashboard {
    constructor() {
        this.cameras = [];
        this.filteredCameras = [];
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.render();
    }

    async loadData() {
        try {
            const response = await fetch('data/prices.json');
            const data = await response.json();
            this.cameras = data.cameras || [];
            this.lastUpdated = data.last_updated || null;
            this.updateLastUpdatedDisplay();
        } catch (error) {
            console.error('Failed to load price data:', error);
            this.cameras = [];
        }
        this.filteredCameras = [...this.cameras];
    }

    updateLastUpdatedDisplay() {
        const element = document.getElementById('lastUpdated');
        if (this.lastUpdated) {
            const date = new Date(this.lastUpdated);
            element.textContent = `Last updated: ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
        } else {
            element.textContent = 'Last updated: Unknown';
        }
    }

    setupEventListeners() {
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filterAndRender();
        });

        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.filterAndRender();
        });

        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.filterAndRender();
        });
    }

    filterAndRender() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const category = document.getElementById('categoryFilter').value;
        const sortBy = document.getElementById('sortBy').value;

        // Filter
        this.filteredCameras = this.cameras.filter(camera => {
            const matchesSearch =
                camera.name.toLowerCase().includes(searchTerm) ||
                camera.model.toLowerCase().includes(searchTerm) ||
                (camera.description && camera.description.toLowerCase().includes(searchTerm));

            const matchesCategory = category === 'all' || camera.category === category;

            return matchesSearch && matchesCategory;
        });

        // Sort
        this.filteredCameras.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'price-asc':
                    return (a.price || Infinity) - (b.price || Infinity);
                case 'price-desc':
                    return (b.price || 0) - (a.price || 0);
                case 'category':
                    return a.category.localeCompare(b.category);
                default:
                    return 0;
            }
        });

        this.render();
    }

    formatPrice(price) {
        if (price === null || price === undefined) {
            return 'Price unavailable';
        }
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(price);
    }

    createCameraCard(camera) {
        const card = document.createElement('div');
        card.className = 'camera-card';

        const hasPrice = camera.price !== null && camera.price !== undefined;
        const priceClass = hasPrice ? 'price' : 'price no-price';
        const priceText = this.formatPrice(camera.price);

        card.innerHTML = `
            <span class="category-badge ${camera.category}">${camera.category}</span>
            <h3>${this.escapeHtml(camera.name)}</h3>
            <p class="model">${this.escapeHtml(camera.model)}</p>
            <p class="${priceClass}">${priceText}</p>
            <p class="source">Source: ${this.escapeHtml(camera.retailer || 'Unknown')}</p>
            <div class="actions">
                ${camera.url ? `<a href="${this.escapeHtml(camera.url)}" target="_blank" rel="noopener noreferrer" class="view-link">View Product</a>` : ''}
            </div>
        `;

        return card;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    render() {
        const grid = document.getElementById('cameraGrid');
        const noResults = document.getElementById('noResults');
        const itemCount = document.getElementById('itemCount');

        grid.innerHTML = '';

        if (this.filteredCameras.length === 0) {
            noResults.style.display = 'block';
            itemCount.textContent = '0 items';
        } else {
            noResults.style.display = 'none';
            itemCount.textContent = `${this.filteredCameras.length} item${this.filteredCameras.length !== 1 ? 's' : ''}`;

            this.filteredCameras.forEach(camera => {
                grid.appendChild(this.createCameraCard(camera));
            });
        }
    }
}

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new CameraDashboard();
});
