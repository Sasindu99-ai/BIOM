class Loader {
  constructor() {
    this.init();
  }

  init() {
    // Add event listeners to all tags that should load content dynamically
    document.querySelectorAll('.dynamic-link').forEach(link => {
      link.addEventListener('click', this.loadContent.bind(this));
    });
  }

  async loadContent(event) {
    event.preventDefault();
    const url = event.currentTarget.href;

    try {
      // Fetch the new content
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.text();

      // Update the URL without reloading the page
      history.pushState({ url }, '', url);

      // Parse the fetched HTML and update the necessary parts of the document
      const parser = new DOMParser();
      const doc = parser.parseFromString(data, 'text/html');

      // Update the main content
      document.querySelector('main').innerHTML = doc.querySelector('main').innerHTML;

      // Update meta tags
      this.updateMetaTags(doc);

      // Update styles
      this.updateStyles(doc);

      // Update scripts
      this.updateScripts(doc);

      // Reinitialize event listeners on new content
      this.init();
    } catch (error) {
      console.error('Failed to load content:', error);
    }
  }

  updateMetaTags(doc) {
    const newMetaTags = doc.querySelectorAll('meta');
    const oldMetaTags = document.querySelectorAll('meta');
    oldMetaTags.forEach(tag => tag.remove());
    newMetaTags.forEach(tag => document.head.appendChild(tag));
  }

  updateStyles(doc) {
    const newStyles = doc.querySelectorAll('link[rel="stylesheet"]');
    const oldStyles = document.querySelectorAll('link[rel="stylesheet"]');
    oldStyles.forEach(style => style.remove());
    newStyles.forEach(style => document.head.appendChild(style));
  }

  updateScripts(doc) {
    const newScripts = doc.querySelectorAll('script');
    const oldScripts = document.querySelectorAll('script');
    oldScripts.forEach(script => script.remove());
    newScripts.forEach(script => {
      const newScript = document.createElement('script');
      newScript.src = script.src;
      document.body.appendChild(newScript);
    });
  }
}

// Instantiate the class
document.addEventListener('DOMContentLoaded', () => {
  new Loader();
});


// Browser back and forward buttons
window.addEventListener('popstate', (event) => {
  if (event.state && event.state.url) {
    new Loader().loadContent({ currentTarget: { href: event.state.url }, preventDefault: () => {} });
  }
});
