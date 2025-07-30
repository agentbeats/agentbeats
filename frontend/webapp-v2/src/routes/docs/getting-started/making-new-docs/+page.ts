export async function load() {
  try {
    const content = await import('./making-new-docs.md');
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