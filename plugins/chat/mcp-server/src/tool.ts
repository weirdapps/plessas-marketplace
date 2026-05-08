export interface Tool {
  name: string;
  description: string;
  inputSchema: object;
  handler: (args: any) => Promise<unknown>;
}
