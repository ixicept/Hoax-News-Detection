declare module 'pdfjs-dist' {
  export const GlobalWorkerOptions: {
    workerSrc: string;
  };
  export function getDocument(
    src: string | Uint8Array | object
  ): {
    promise: Promise<any>;
  };
}
