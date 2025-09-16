// DOM elements
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const searchSummary = document.getElementById('searchSummary');
const productsContainer = document.getElementById('productsContainer');
const errorMessage = document.getElementById('errorMessage');

// Authentication elements
const authToggleBtn = document.getElementById('authToggleBtn');
const authModal = document.getElementById('authModal');
const closeModal = document.getElementById('closeModal');
const authForm = document.getElementById('authForm');
const enableAuth = document.getElementById('enableAuth');
const authFields = document.getElementById('authFields');
const emailInput = document.getElementById('emailInput');
const passwordInput = document.getElementById('passwordInput');
const persistentSession = document.getElementById('persistentSession');
const statusIndicator = document.getElementById('statusIndicator');
const testAuthBtn = document.getElementById('testAuthBtn');
const saveAuthBtn = document.getElementById('saveAuthBtn');
const clearAuthBtn = document.getElementById('clearAuthBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');

// API configuration
const API_BASE_URL = 'http://localhost:5000';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Ensure loading overlay is hidden on page load
    hideLoadingOverlay();
    
    searchForm.addEventListener('submit', handleSearch);
    initializeAuthentication();
});

// Initialize authentication functionality
function initializeAuthentication() {
    try {
        // Event listeners
        authToggleBtn.addEventListener('click', openAuthModal);
        closeModal.addEventListener('click', closeAuthModal);
        enableAuth.addEventListener('change', toggleAuthFields);
        testAuthBtn.addEventListener('click', testAuthentication);
        saveAuthBtn.addEventListener('click', saveAuthConfig);
        clearAuthBtn.addEventListener('click', clearAuthData);
        
        // Close modal when clicking outside
        authModal.addEventListener('click', function(event) {
            if (event.target === authModal) {
                closeAuthModal();
            }
        });
        
        // Load current auth config
        loadAuthConfig();
        // Also refresh status from server
        refreshAuthStatus();
    } catch (error) {
        console.error('Error initializing authentication:', error);
        // Ensure loading overlay is hidden even if there's an error
        hideLoadingOverlay();
    }
}

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

// Authentication Functions
async function loadAuthConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth-config`);
        const data = await response.json();
        
        if (data.success) {
            const config = data.config;
            
            // Update form fields
            enableAuth.checked = config.enabled;
            emailInput.value = config.email || '';
            persistentSession.checked = config.persistent_session;
            
            // Update UI
            toggleAuthFields();
            // Persist has_password info for enabling Test button without exposing it
            statusIndicator.dataset.hasPassword = String(!!config.has_password);
            // Don't assume authenticated just because password exists; ask backend
            updateAuthStatus({ enabled: config.enabled, email: config.email, has_password: config.has_password, is_logged_in: false, account_info: '' });
            updateTestButton();
            // Fetch real status
            refreshAuthStatus();
        }
    } catch (error) {
        console.error('Error loading auth config:', error);
        // Ensure loading overlay is hidden even if there's an error
        hideLoadingOverlay();
    }
}

async function refreshAuthStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth-status`);
        const data = await response.json();
        if (data && data.success) {
            updateAuthStatus({
                enabled: data.enabled,
                email: data.email,
                has_password: null, // unknown here; UI doesn't need it
                is_logged_in: data.is_logged_in,
                account_info: data.account_info
            });
        }
    } catch (e) {
        // Non-fatal
        console.warn('Auth status check failed');
        // Ensure loading overlay is hidden even if there's an error
        hideLoadingOverlay();
    }
}

function openAuthModal() {
    authModal.classList.remove('hidden');
    authModal.classList.add('fade-in');
    loadAuthConfig(); // Refresh config when opening
}

function closeAuthModal() {
    authModal.classList.add('hidden');
}

function toggleAuthFields() {
    const enabled = enableAuth.checked;
    authFields.classList.toggle('hidden', !enabled);
    updateTestButton();
    
    if (enabled) {
        emailInput.focus();
    }
}

function updateAuthStatus(config) {
    if (!config.enabled) {
        statusIndicator.textContent = '🔓 Not Authenticated';
        statusIndicator.className = 'status-indicator not-authenticated';
        return;
    }

    if (config.is_logged_in) {
        const label = config.account_info ? config.account_info : `Authenticated as ${config.email || ''}`;
        statusIndicator.textContent = `🔐 ${label}`;
        statusIndicator.className = 'status-indicator authenticated';
        return;
    }

    // Enabled but not logged in or unknown status
    statusIndicator.textContent = '⚠️ Authentication Enabled (Not logged in)';
    statusIndicator.className = 'status-indicator';
}

function updateTestButton() {
    const enabled = enableAuth.checked;
    const hasEmail = emailInput.value.trim() !== '';
    // Allow enabling test button if either input has password or backend indicates one is stored
    const inputHasPassword = passwordInput.value.trim() !== '';
    // Persist a flag when backend said password exists via loadAuthConfig
    const storedHasPassword = statusIndicator.dataset.hasPassword === 'true';

    testAuthBtn.disabled = !enabled || !hasEmail || !(inputHasPassword || storedHasPassword);
}

async function saveAuthConfig() {
    try {
        setButtonLoading(saveAuthBtn, true);
        
        const config = {
            enabled: enableAuth.checked,
            email: emailInput.value.trim(),
            persistent_session: persistentSession.checked
        };
        
        // Only include password if it's filled
        if (passwordInput.value.trim()) {
            config.password = passwordInput.value;
        }
        
        const response = await fetch(`${API_BASE_URL}/auth-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessMessage('Authentication settings saved successfully!');
            loadAuthConfig(); // Refresh the display
        } else {
            showError(data.error || 'Failed to save authentication settings');
        }
    } catch (error) {
        console.error('Error saving auth config:', error);
        showError('Failed to save authentication settings. Please try again.');
    } finally {
        setButtonLoading(saveAuthBtn, false);
    }
}

async function testAuthentication() {
    try {
        setButtonLoading(testAuthBtn, true);
        showLoadingOverlay('Testing authentication...');
        
        const response = await fetch(`${API_BASE_URL}/test-auth`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessMessage(`Authentication successful! ${data.account_info || ''}`);
        } else {
            showError(data.error || 'Authentication test failed');
        }
    } catch (error) {
        console.error('Error testing auth:', error);
        showError('Failed to test authentication. Please try again.');
    } finally {
        setButtonLoading(testAuthBtn, false);
        hideLoadingOverlay();
    }
}

async function clearAuthData() {
    if (!confirm('Are you sure you want to clear all authentication data? This action cannot be undone.')) {
        return;
    }
    
    try {
        setButtonLoading(clearAuthBtn, true);
        
        const response = await fetch(`${API_BASE_URL}/clear-auth`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reset form
            enableAuth.checked = false;
            emailInput.value = '';
            passwordInput.value = '';
            persistentSession.checked = true;
            
            toggleAuthFields();
            loadAuthConfig(); // Refresh the display
            
            showSuccessMessage('Authentication data cleared successfully!');
        } else {
            showError(data.error || 'Failed to clear authentication data');
        }
    } catch (error) {
        console.error('Error clearing auth data:', error);
        showError('Failed to clear authentication data. Please try again.');
    } finally {
        setButtonLoading(clearAuthBtn, false);
    }
}

// UI Helper Functions
function setButtonLoading(button, loading) {
    button.disabled = loading;
    if (loading) {
        button.dataset.originalText = button.textContent;
        button.textContent = '⏳ Loading...';
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

function showLoadingOverlay(text) {
    loadingText.textContent = text;
    loadingOverlay.classList.remove('hidden');
}

function hideLoadingOverlay() {
    loadingOverlay.classList.add('hidden');
}

function showSuccessMessage(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #d4edda;
        color: #155724;
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        z-index: 3000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        animation: slideInRight 0.3s ease-out;
    `;
    successDiv.textContent = message;
    
    document.body.appendChild(successDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        successDiv.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 300);
    }, 3000);
}

// Add CSS animations for success messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Update keyboard shortcuts to include auth modal
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + K to focus search input
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
    }

    // Escape to clear search or close modal
    if (event.key === 'Escape') {
        if (!authModal.classList.contains('hidden')) {
            closeAuthModal();
        } else {
            searchInput.value = '';
            hideResults();
            hideError();
            searchInput.focus();
        }
    }
    
    // Ctrl/Cmd + A to open auth settings
    if ((event.ctrlKey || event.metaKey) && event.key === 'a' && event.shiftKey) {
        event.preventDefault();
        openAuthModal();
    }
});

// Add input validation for auth fields
emailInput.addEventListener('input', updateTestButton);
passwordInput.addEventListener('input', updateTestButton);
