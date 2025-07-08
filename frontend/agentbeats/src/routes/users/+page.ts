import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  try {
    const res = await fetch('http://localhost:9000/users');
    const rawData = await res.json();
    return { users: rawData };
  } catch (error) {
    console.error('Failed to fetch users:', error);
    return { users: [] };
  }
}; 