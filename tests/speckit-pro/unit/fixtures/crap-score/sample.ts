export function simple(x: number): number {
  return x + 1;
}

export function tangled(a: boolean, b: boolean, c: boolean, d: boolean, e: boolean, f: boolean, g: boolean, h: boolean, i: number): number {
  if (a && b) return 1;
  if (c || d) return 2;
  if (e) return 3;
  if (f) return 4;
  if (g) return 5;
  if (h) return 6;
  return i;
}
