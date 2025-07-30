export async function load() {
  try {
    const cliDoc = await import('./cli-reference.md');
    return {
      content: cliDoc.default
    };
  } catch (error) {
    console.error('Error loading .md file:', error);
    return {
      content: '<h1>CLI Reference</h1><p>Failed to load documentation.</p>'
    };
  }
} 