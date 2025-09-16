// DOM elements
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const searchSummary = document.getElementById('searchSummary');
const productsContainer = document.getElementById('productsContainer');
const errorMessage = document.getElementById('errorMessage');

// API configuration
const API_BASE_URL = 'http://localhost:5001';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    searchForm.addEventListener('submit', handleSearch);
});

// Handle search form submission
async function handleSearch(event) {
    event.preventDefault();

    const keyword = searchInput.value.trim();
    if (!keyword) return;

    // Show loading state
    setLoadingState(true);
    hideError();
    hideResults();

    try {
        const response = await fetch(`${API_BASE_URL}/search-reviews?q=${encodeURIComponent(keyword)}&max_products=3`);
        const data = await response.json();

        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'Search failed. Please try again.');
        }
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to connect to the server. Please make sure the backend is running.');
    } finally {
        setLoadingState(false);
    }
}

// Set loading state for search button
function setLoadingState(loading) {
    searchButton.classList.toggle('loading', loading);
    searchButton.disabled = loading;
    searchInput.disabled = loading;
}

    // Display search results
function displayResults(data) {
    // Update search summary
    searchSummary.innerHTML = `
        <h2>Search Results for "${data.search_term}"</h2>
        <p>Found ${data.total_products} products with ${data.total_reviews} total reviews</p>
        ${data.excel_download_url ? `<p><a href="${data.excel_download_url}" target="_blank" class="download-all-btn">📊 Download All Reviews (Excel)</a></p>` : ''}
    `;

    // Clear previous results
    productsContainer.innerHTML = '';

    // Create product cards
    data.products.forEach(product => {
        const productCard = createProductCard(product);
        productsContainer.appendChild(productCard);
    });

    // Show results section
    resultsSection.classList.remove('hidden');
    resultsSection.classList.add('fade-in');
}

// Create a product card element
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    card.innerHTML = `
        <div class="product-summary">
            <div class="product-info">
                <div class="product-title">${escapeHtml(product.title)}</div>
                <a href="${product.url}" target="_blank" class="product-url">
                    View on Amazon ↗
                </a>
            </div>
            <div class="product-stats">
                <span class="review-count">${product.reviews_count} reviews</span>
                <span class="success-indicator ${product.success ? 'success' : 'error'}">
                    ${product.success ? '✅' : '❌'}
                </span>
            </div>
        </div>

    `;

    return card;
}

// Create a review item element
function createReviewItem(review) {
    const reviewItem = document.createElement('div');
    reviewItem.className = 'review-item';

    const stars = generateStars(review.rating);

    reviewItem.innerHTML = `
        <div class="review-header">
            <span class="reviewer-name">${escapeHtml(review.reviewer_name || 'Anonymous')}</span>
            <div class="review-rating">
                <span class="stars">${stars}</span>
                <span class="rating-number">${review.rating || 'N/A'}</span>
            </div>
        </div>
        <div class="review-meta">
            <span>📅 ${review.date || 'Date not available'}</span>
            ${review.helpful_votes ? `<span>👍 ${review.helpful_votes} found helpful</span>` : ''}
        </div>
        <div class="review-text">${escapeHtml(review.text || 'No review text available.')}</div>
    `;

    return reviewItem;
}

// Generate star rating display
function generateStars(rating) {
    if (!rating) return '☆☆☆☆☆';

    const numRating = parseFloat(rating);
    let stars = '';

    for (let i = 1; i <= 5; i++) {
        if (i <= numRating) {
            stars += '★';
        } else if (i - 0.5 <= numRating) {
            stars += '☆'; // Could use half star, but keeping simple
        } else {
            stars += '☆';
        }
    }

    return stars;
}

// Toggle product card expansion
function toggleProductExpansion(card) {
    card.classList.toggle('expanded');
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    errorMessage.classList.add('fade-in');
}

// Hide error message
function hideError() {
    errorMessage.classList.add('hidden');
}

// Hide results section
function hideResults() {
    resultsSection.classList.add('hidden');
}



// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add some helpful keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + K to focus search input
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
    }

    // Escape to clear search
    if (event.key === 'Escape') {
        searchInput.value = '';
        hideResults();
        hideError();
        searchInput.focus();
    }
});
