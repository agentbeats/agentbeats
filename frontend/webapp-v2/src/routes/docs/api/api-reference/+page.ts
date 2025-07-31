export async function load() {
  try {
    // Use fetch to get the YAML file from the static assets
    const response = await fetch('/backend_openapi.yaml');
    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI spec: ${response.statusText}`);
    }
    const yamlText = await response.text();
    
    return {
      spec: yamlText
    };
  } catch (error) {
    console.error('Failed to load API docs:', error);
    return {
      spec: null
    };
  }
} 