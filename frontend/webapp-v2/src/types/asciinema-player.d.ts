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

