let googleTranslateInstance = null;

    function googleTranslateElementInit() {
      googleTranslateInstance = new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,ar',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
      }, 'google_translate_element');
    }

    function switchLanguage(select) {
      const lang = select.value;

      if (lang === 'en') {
        document.cookie = "googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        document.cookie = "googtrans=; domain=" + location.hostname + "; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
      } else {
        const cookieValue = `/en/${lang}`;
        document.cookie = `googtrans=${cookieValue}; path=/;`;
        document.cookie = `googtrans=${cookieValue}; domain=${location.hostname}; path=/;`;
      }

      window.location.reload();
    }

    // Blog category filtering
    document.addEventListener('DOMContentLoaded', function() {
      const categoryBtns = document.querySelectorAll('.category-btn');
      const blogCards = document.querySelectorAll('.blog-card');

      categoryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
          // Update active button
          categoryBtns.forEach(b => b.classList.remove('active'));
          this.classList.add('active');

          const category = this.dataset.category;
          
          // Filter blog cards
          blogCards.forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
              card.style.display = 'block';
            } else {
              card.style.display = 'none';
            }
          });
        });
      });

      // Hide Google Translate UI
      const hideGoogleTranslateUI = () => {
        const selectors = [
          '.goog-te-banner-frame',
          '.goog-te-balloon-frame',
          '#goog-gt-tt',
          '.goog-te-menu-value',
          '.goog-te-gadget-icon',
          '.goog-te-gadget',
          '.goog-te-combo',
          '.skiptranslate'
        ];

        selectors.forEach(selector => {
          const el = document.querySelector(selector);
          if (el) {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
            el.style.height = '0';
            el.style.width = '0';
            el.style.overflow = 'hidden';
            el.style.position = 'absolute';
            el.style.top = '-9999px';
            el.style.left = '-9999px';
          }
        });
      };

      // Force LTR direction
      const forceLTR = () => {
        document.documentElement.setAttribute("dir", "ltr");
        document.body.setAttribute("dir", "ltr");
      };

      // Initialize
      if (!document.cookie.includes("googtrans")) {
        document.cookie = "googtrans=/en/en; path=/;";
        document.cookie = "googtrans=/en/en; domain=" + location.hostname + "; path=/;";
      }

      const select = document.getElementById("lang-select");
      if (document.cookie.includes("googtrans=/en/ar")) {
        select.value = "ar";
      } else {
        select.value = "en";
      }

      if (!document.querySelector('script[src*="translate.google.com"]')) {
        const script = document.createElement('script');
        script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        document.body.appendChild(script);
      }

      // Mutation observer for Google Translate elements
      const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
          if (mutation.addedNodes) {
            hideGoogleTranslateUI();
          }
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      window.addEventListener('load', () => {
        setTimeout(() => {
          forceLTR();
        }, 1000);
      });
    });
    // Update the category filtering script
document.addEventListener('DOMContentLoaded', function() {
    const categoryBtns = document.querySelectorAll('.category-btn');
    const blogCards = document.querySelectorAll('.blog-card');

    categoryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active button
            categoryBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const category = this.dataset.category;
            
            // Filter blog cards
            blogCards.forEach(card => {
                if (category === 'all' || card.dataset.category === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
});