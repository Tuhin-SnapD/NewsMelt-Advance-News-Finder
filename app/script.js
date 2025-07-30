// Enhanced JavaScript for News Viewer with modern UI/UX features

// DOM Elements
const elements = {
  btn1: document.getElementById("btn1"),
  btn2: document.getElementById("btn2"),
  btn3: document.getElementById("btn3"),
  btn4: document.getElementById("btn4"),
  exportBtn: document.getElementById("exportBtn"),
  content: document.getElementById("content"),
  image: document.getElementById("image"),
  imageContainer: document.getElementById("image-container"),
  loadingOverlay: document.getElementById("loadingOverlay"),
  categoryBadge: document.getElementById("categoryBadge"),
  timestamp: document.getElementById("timestamp"),
  articlesCount: document.getElementById("articlesCount"),
  topicsCount: document.getElementById("topicsCount"),
  trendingScore: document.getElementById("trendingScore"),
  lastUpdated: document.getElementById("lastUpdated"),
  aboutLink: document.getElementById("aboutLink"),
  aboutModal: document.getElementById("aboutModal"),
  closeModal: document.getElementById("closeModal")
};

// Category configurations with available visualizations
const categories = {
  business: { 
    text: "business.txt", 
    main: "business.png", 
    heatmap: "business_heatmap.png", 
    wordcloud: "business_wordcloud.png",
    icon: "fas fa-briefcase", 
    color: "#10b981",
    description: "Market trends & financial insights"
  },
  entertainment: { 
    text: "entertainment.txt", 
    main: "entertainment.png", 
    heatmap: "entertainment_heatmap.png", 
    wordcloud: "entertainment_wordcloud.png",
    icon: "fas fa-film", 
    color: "#f59e0b",
    description: "Media, arts & cultural analysis"
  },
  health: { 
    text: "health.txt", 
    main: "health.png", 
    heatmap: "health_heatmap.png", 
    wordcloud: "health_wordcloud.png",
    icon: "fas fa-heartbeat", 
    color: "#ef4444",
    description: "Medical & wellness insights",
    hasInsufficientContent: false
  },
  science: { 
    text: "science.txt", 
    main: "science.png", 
    heatmap: "science_heatmap.png", 
    wordcloud: "science_wordcloud.png",
    icon: "fas fa-flask", 
    color: "#8b5cf6",
    description: "Research & technological advances",
    hasInsufficientContent: false
  }
};

// Current state
let currentCategory = null;
let currentVizType = 'main';

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, setting up event listeners...'); // Debug log
  console.log('Found elements:', {
    btn1: !!elements.btn1,
    btn2: !!elements.btn2,
    btn3: !!elements.btn3,
    btn4: !!elements.btn4
  }); // Debug log
  
  // Add enhanced click handlers with animations
  if (elements.btn1) {
    elements.btn1.addEventListener("click", () => {
      addClickAnimation(elements.btn1);
      loadCategory("business");
    });
  } else {
    console.error('Business button (btn1) not found in DOM');
  }
  
  if (elements.btn2) {
    elements.btn2.addEventListener("click", () => {
      addClickAnimation(elements.btn2);
      loadCategory("entertainment");
    });
  } else {
    console.error('Entertainment button (btn2) not found in DOM');
  }
  
  if (elements.btn3) {
    elements.btn3.addEventListener("click", () => {
      addClickAnimation(elements.btn3);
      loadCategory("health");
    });
  } else {
    console.error('Health button (btn3) not found in DOM');
  }
  if (elements.btn4) {
    elements.btn4.addEventListener("click", () => {
      console.log('Science button clicked!'); // Debug log
      addClickAnimation(elements.btn4);
      loadCategory("science");
    });
  } else {
    console.error('Science button (btn4) not found in DOM');
  }
  
  elements.exportBtn.addEventListener("click", exportReport);
  elements.aboutLink.addEventListener("click", showAboutModal);
  elements.closeModal.addEventListener("click", hideAboutModal);
  
  // Visualization tab handlers
  document.querySelectorAll('.viz-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const vizType = tab.dataset.viz;
      console.log('Switching to visualization:', vizType); // Debug log
      switchVisualization(vizType);
    });
  });
  
  // Initialize with placeholder content
  showPlaceholder();
  
  // Add welcome animation
  setTimeout(() => {
    document.querySelector('.header').style.animation = 'fadeIn 1s ease-out';
  }, 100);
  
  // Ensure visualization tabs are properly set up (fallback)
  setTimeout(() => {
    setupVisualizationTabs();
  }, 200);
});

// Add click animation function
function addClickAnimation(element) {
  element.style.animation = 'bounce 0.6s ease-in-out';
  setTimeout(() => {
    element.style.animation = '';
  }, 600);
}

// Setup visualization tabs with proper event listeners
function setupVisualizationTabs() {
  const tabs = document.querySelectorAll('.viz-tab');
  console.log('Setting up visualization tabs, found:', tabs.length); // Debug log
  
  tabs.forEach(tab => {
    // Remove any existing listeners to prevent duplicates
    tab.removeEventListener('click', handleVizTabClick);
    // Add new listener
    tab.addEventListener('click', handleVizTabClick);
  });
}

// Handle visualization tab clicks
function handleVizTabClick(e) {
  e.preventDefault();
  e.stopPropagation();
  
  const vizType = this.dataset.viz;
  console.log('Visualization tab clicked:', vizType); // Debug log
  
  if (vizType) {
    switchVisualization(vizType);
  }
}

// Utility Functions
function showLoading() {
  elements.loadingOverlay.classList.add('show');
}

function hideLoading() {
  elements.loadingOverlay.classList.remove('show');
}

function showPlaceholder() {
  elements.content.innerHTML = `
    <div class="placeholder">
      <i class="fas fa-chart-bar"></i>
      <p>Select a category above to view comprehensive news analysis with data visualizations</p>
    </div>
  `;
  elements.imageContainer.innerHTML = `
    <div class="image-placeholder">
      <i class="fas fa-chart-pie"></i>
      <p>Select a category to view visualizations</p>
    </div>
  `;
  updateAnalytics({ articles: 0, topics: 0, trending: 0, updated: '-' });
}

function showError(message) {
  elements.content.innerHTML = `
    <div class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <p>${message}</p>
    </div>
  `;
}

function updateContentTitle(category) {
  const contentTitle = document.querySelector('.content-title');
  if (contentTitle) {
    contentTitle.textContent = `${category.charAt(0).toUpperCase() + category.slice(1)} News Analysis Dashboard`;
  }
}

function updateCategoryBadge(category) {
  if (elements.categoryBadge) {
    elements.categoryBadge.textContent = category.charAt(0).toUpperCase() + category.slice(1);
  }
}

function updateTimestamp() {
  if (elements.timestamp) {
    const now = new Date();
    elements.timestamp.textContent = now.toLocaleString();
  }
}

function updateAnalytics(data) {
  if (elements.articlesCount) elements.articlesCount.textContent = data.articles;
  if (elements.topicsCount) elements.topicsCount.textContent = data.topics;
  if (elements.trendingScore) elements.trendingScore.textContent = data.trending + '%';
  if (elements.lastUpdated) elements.lastUpdated.textContent = data.updated;
}

function animateContent() {
  const contentCard = document.querySelector('.content-card');
  contentCard.style.animation = 'none';
  contentCard.offsetHeight; // Trigger reflow
  contentCard.style.animation = 'fadeIn 0.6s ease-out';
}

// Load category data
async function loadCategory(categoryName) {
  try {
    console.log('loadCategory called with:', categoryName); // Debug log
    showLoading();
    currentCategory = categoryName;
    const category = categories[categoryName];
    console.log('Category config:', category); // Debug log
    
    updateContentTitle(categoryName);
    updateCategoryBadge(categoryName);
    updateTimestamp();
    
    // Clear previous content
    elements.content.innerHTML = '';
    elements.imageContainer.innerHTML = '';
    
    // Check if category has insufficient content
    if (category.hasInsufficientContent) {
      elements.content.innerHTML = `
        <div class="news-content">
          <div class="insufficient-content">
            <i class="fas fa-exclamation-triangle"></i>
            <h4>Insufficient Content Available</h4>
            <p>There isn't enough ${categoryName} news content available for analysis at the moment.</p>
            <div class="insufficient-content-actions">
              <p><strong>To fix this issue:</strong></p>
              <ol>
                <li>Set up your API keys in the <code>.env</code> file</li>
                <li>Run the news pipeline: <code>python run.py</code></li>
                <li>Or try another category that has available data</li>
              </ol>
              <div class="category-suggestion">
                <p><strong>Available categories with data:</strong></p>
                <div class="suggestion-buttons">
                  <button onclick="loadCategory('business')" class="suggestion-btn">
                    <i class="fas fa-briefcase"></i> Business
                  </button>
                  <button onclick="loadCategory('entertainment')" class="suggestion-btn">
                    <i class="fas fa-film"></i> Entertainment
                  </button>
                  <button onclick="loadCategory('science')" class="suggestion-btn">
                    <i class="fas fa-flask"></i> Science
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
      
      // Show placeholder for visualizations
      elements.imageContainer.innerHTML = `
        <div class="image-placeholder">
          <i class="fas fa-chart-line"></i>
          <p>No visualizations available</p>
          <small>Content needs to be generated first</small>
        </div>
      `;
      
      // Update analytics for insufficient content
      updateAnalytics({ articles: 0, topics: 0, trending: 0, updated: 'No data' });
      
    } else {
      // Fetch text and main visualization concurrently (if available)
      const promises = [fetch(`../dataset/final/${category.text}`)];
      
      if (category.main) {
        promises.push(fetch(`../dataset/graphs/${category.main}`));
      }
      
      const responses = await Promise.allSettled(promises);
      const textResponse = responses[0];
      const imageResponse = category.main ? responses[1] : { status: 'rejected' };
      
      // Handle text response
      if (textResponse.status === 'fulfilled' && textResponse.value.ok) {
        const text = await textResponse.value.text();
        
        // Check if content is insufficient
        if (text.includes("Insufficient content") || text.trim().length < 20 || text.includes("Unable to load")) {
          elements.content.innerHTML = `
            <div class="news-content">
              <div class="insufficient-content">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>Insufficient Content</h4>
                <p>There isn't enough ${categoryName} news content available for analysis at the moment. Please try another category or check back later.</p>
                <div class="insufficient-content-actions">
                  <p><strong>To fix this issue:</strong></p>
                  <ol>
                    <li>Set up your API keys in the <code>.env</code> file</li>
                    <li>Run the news pipeline: <code>python run.py</code></li>
                    <li>Or try another category that has available data</li>
                  </ol>
                  <div class="category-suggestion">
                    <p><strong>Available categories with data:</strong></p>
                    <div class="suggestion-buttons">
                      <button onclick="loadCategory('business')" class="suggestion-btn">
                        <i class="fas fa-briefcase"></i> Business
                      </button>
                      <button onclick="loadCategory('entertainment')" class="suggestion-btn">
                        <i class="fas fa-film"></i> Entertainment
                      </button>
                      <button onclick="loadCategory('science')" class="suggestion-btn">
                        <i class="fas fa-flask"></i> Science
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          `;
        } else {
          // Format the text with proper line breaks and paragraphs
          const formattedText = text
            .replace(/\. /g, '.\n\n')
            .replace(/\n\n+/g, '\n\n')
            .trim();
          
          elements.content.innerHTML = `
            <div class="news-content">
              <p>${formattedText}</p>
            </div>
          `;
        }
      } else {
        showError(`Unable to load ${categoryName} news content. Please try again.`);
      }
      
      // Handle image response
      if (imageResponse.status === 'fulfilled' && imageResponse.value.ok) {
        const imageBlob = await imageResponse.value.blob();
        const imageURL = URL.createObjectURL(imageBlob);
        elements.imageContainer.innerHTML = `<img id="image" src="${imageURL}" alt="${categoryName} visualization" class="news-image" />`;
        
        // Add loading animation for image
        const img = elements.imageContainer.querySelector('#image');
        if (img) {
          img.onload = function() {
            this.style.opacity = '0';
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
              this.style.transition = 'all 0.3s ease-out';
              this.style.opacity = '1';
              this.style.transform = 'scale(1)';
            }, 100);
          };
          
          // Handle image load errors
          img.onerror = function() {
            elements.imageContainer.innerHTML = `
              <div class="image-placeholder">
                <i class="fas fa-image"></i>
                <p>No visualization available</p>
                <small>Image failed to load</small>
              </div>
            `;
          };
        }
      } else {
        // Show placeholder for missing image
        elements.imageContainer.innerHTML = `
          <div class="image-placeholder">
            <i class="fas fa-image"></i>
            <p>No visualization available</p>
            <small>File not found</small>
          </div>
        `;
      }
      
      // Update analytics with mock data
      const mockAnalytics = {
        articles: Math.floor(Math.random() * 50) + 20,
        topics: Math.floor(Math.random() * 15) + 5,
        trending: Math.floor(Math.random() * 40) + 60,
        updated: new Date().toLocaleString()
      };
      updateAnalytics(mockAnalytics);
    }
    
    // Animate content appearance
    animateContent();
    
    // Ensure visualization tabs are properly set up after loading content
    setupVisualizationTabs();
    
    // Scroll to content smoothly
    document.querySelector('.content-section').scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });
    
  } catch (error) {
    console.error('Error loading category:', error);
    showError('An unexpected error occurred. Please try again.');
  } finally {
    hideLoading();
  }
}

// Switch visualization type
async function switchVisualization(vizType) {
  console.log('switchVisualization called with:', vizType); // Debug log
  console.log('currentCategory:', currentCategory); // Debug log
  
  if (!currentCategory) {
    console.log('No current category selected'); // Debug log
    return;
  }
  
  // Update active tab
  document.querySelectorAll('.viz-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  const activeTab = document.querySelector(`[data-viz="${vizType}"]`);
  if (activeTab) {
    activeTab.classList.add('active');
    console.log('Updated active tab to:', vizType); // Debug log
  } else {
    console.log('Could not find tab with data-viz:', vizType); // Debug log
  }
  
  currentVizType = vizType;
  const category = categories[currentCategory];
  const imageFile = category[vizType];
  
  console.log('Category:', category); // Debug log
  console.log('Image file:', imageFile); // Debug log
  
  if (!imageFile) {
    elements.imageContainer.innerHTML = `
      <div class="image-placeholder">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Visualization not available for this category</p>
        <small>Try another category that has data visualizations</small>
      </div>
    `;
    return;
  }
  
  try {
    showLoading();
    
    const response = await fetch(`../dataset/graphs/${imageFile}`);
    
    if (response.ok) {
      const imageBlob = await response.blob();
      const imageURL = URL.createObjectURL(imageBlob);
      elements.imageContainer.innerHTML = `<img id="image" src="${imageURL}" alt="${currentCategory} ${vizType}" class="news-image" />`;
      
      // Add loading animation for image
      const img = elements.imageContainer.querySelector('#image');
      if (img) {
        img.onload = function() {
          this.style.opacity = '0';
          this.style.transform = 'scale(0.95)';
          setTimeout(() => {
            this.style.transition = 'all 0.3s ease-out';
            this.style.opacity = '1';
            this.style.transform = 'scale(1)';
          }, 100);
        };
        
        // Handle image load errors
        img.onerror = function() {
          elements.imageContainer.innerHTML = `
            <div class="image-placeholder">
              <i class="fas fa-image"></i>
              <p>Visualization not available</p>
              <small>Image failed to load</small>
            </div>
          `;
        };
      }
    } else {
      elements.imageContainer.innerHTML = `
        <div class="image-placeholder">
          <i class="fas fa-image"></i>
          <p>Visualization not available</p>
          <small>File not found</small>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading visualization:', error);
    elements.imageContainer.innerHTML = `
      <div class="image-placeholder">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Error loading visualization</p>
        <small>Network error</small>
      </div>
    `;
  } finally {
    hideLoading();
  }
}

// Export report functionality
function exportReport() {
  if (!currentCategory) {
    alert('Please select a category first to export a report.');
    return;
  }
  
  const category = categories[currentCategory];
  const reportData = {
    category: currentCategory,
    timestamp: new Date().toISOString(),
    visualization: currentVizType,
    analytics: {
      articles: elements.articlesCount.textContent,
      topics: elements.topicsCount.textContent,
      trending: elements.trendingScore.textContent,
      updated: elements.lastUpdated.textContent
    }
  };
  
  const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentCategory}_news_report_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  // Show success feedback
  const exportBtn = elements.exportBtn;
  const originalText = exportBtn.innerHTML;
  exportBtn.innerHTML = '<i class="fas fa-check"></i><span>Exported!</span>';
  exportBtn.style.background = 'linear-gradient(135deg, #10b981, #34d399)';
  
  setTimeout(() => {
    exportBtn.innerHTML = originalText;
    exportBtn.style.background = 'linear-gradient(135deg, var(--secondary-color), #34d399)';
  }, 2000);
}

// Modal functions
function showAboutModal() {
  elements.aboutModal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function hideAboutModal() {
  elements.aboutModal.classList.remove('show');
  document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
elements.aboutModal.addEventListener('click', (e) => {
  if (e.target === elements.aboutModal) {
    hideAboutModal();
  }
});







// Add keyboard navigation support
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    hideLoading();
    hideAboutModal();
  }
  
  // Add number keys for quick category selection
  if (event.key >= '1' && event.key <= '4') {
    const categoryIndex = parseInt(event.key) - 1;
    const categoryButtons = [elements.btn1, elements.btn2, elements.btn3, elements.btn4];
    const categoryNames = ['business', 'entertainment', 'health', 'science'];
    
    if (categoryButtons[categoryIndex]) {
      // Add click animation
      categoryButtons[categoryIndex].style.animation = 'bounce 0.6s ease-in-out';
      setTimeout(() => {
        categoryButtons[categoryIndex].style.animation = '';
      }, 600);
      
      loadCategory(categoryNames[categoryIndex]);
    }
  }
});

// Add touch/swipe support for mobile
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', function(event) {
  touchStartX = event.changedTouches[0].screenX;
});

document.addEventListener('touchend', function(event) {
  touchEndX = event.changedTouches[0].screenX;
  handleSwipe();
});

function handleSwipe() {
  const swipeThreshold = 50;
  const diff = touchStartX - touchEndX;
  
  if (Math.abs(diff) > swipeThreshold) {
    // Swipe detected - could be used for category navigation
    console.log('Swipe detected:', diff > 0 ? 'left' : 'right');
  }
}
