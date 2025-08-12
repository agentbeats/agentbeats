// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};

// Types for packages without TS declarations
declare module 'asciinema-player' {
  const AsciinemaPlayer: {
    create: (
      src: string,
      container: HTMLElement,
      options?: Record<string, any>
    ) => unknown;
  };
  export default AsciinemaPlayer;
}
