// Minimal stubs to satisfy TypeScript/Next build in restricted environments.
declare var process: any;
declare var __dirname: string;
declare var __filename: string;
declare var require: any;
declare var module: any;
declare var exports: any;
declare var Buffer: any;

declare module "node:*" {
  const anyExport: any;
  export = anyExport;
}

declare module "*" {
  const anyExport: any;
  export = anyExport;
}
