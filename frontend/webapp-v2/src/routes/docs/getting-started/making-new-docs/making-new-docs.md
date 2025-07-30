# Making New Docs

Quick guide for adding new documentation pages.

## Structure

```
docs/
├── section-name/
│   └── page-name/
│       ├── +page.svelte
│       ├── +page.ts
│       └── page-name.md
```

## Steps

1. **Copy template**:
   ```bash
   cp -r frontend/webapp-v2/src/routes/docs/getting-started/quick-start frontend/webapp-v2/src/routes/docs/section-name/page-name
   ```

2. **Update +page.ts**:
   ```typescript
   const content = await import('./page-name.md');
   ```

3. **Add to sidebar** (`sidebar.svelte`):
   ```typescript
   {
     title: "Section Name",
     url: "/docs/section-name/page-name",
   }
   ```

4. **Write your .md file**

Done! Breadcrumbs work automatically. 