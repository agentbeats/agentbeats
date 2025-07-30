export async function load() {
  try {
    const content = await import('./quick-start.md');
    return {
      content: content.default
    };
  } catch (error) {
    console.error('Error loading .md file:', error);
    return {
      content: null
    };
  }
} 