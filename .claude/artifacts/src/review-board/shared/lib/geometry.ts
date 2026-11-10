export interface Point {
  x: number;
  y: number;
}
export interface Sized {
  width: number;
  height: number;
}
export type Rect = Point & Sized;
