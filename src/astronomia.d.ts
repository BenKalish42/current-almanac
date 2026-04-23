/* Minimal shims: astronomia ships JS without .d.ts for subpath exports. */
declare module "astronomia/julian" {
  export function DateToJD(date: Date): number;
  export function DateToJDE(date: Date): number;
}
declare module "astronomia/moonposition" {
  const moon: {
    position(
      jde: number,
    ): { lon: number; lat: number; range: number };
  };
  export default moon;
}
declare module "astronomia/planetposition" {
  export class Planet {
    constructor(vsop: unknown);
    position(jd: number): { lon: number; lat: number; range: number };
  }
  export function toFK5(lon: number, lat: number, jde: number): { lon: number; lat: number };
}
declare module "astronomia/nutation" {
  const n: {
    meanObliquity(jde: number): number;
    nutation(jde: number): [number, number];
  };
  export default n;
}
declare module "astronomia/sidereal" {
  const s: { apparent(jd: number): number };
  export default s;
}
declare module "astronomia/data" {
  const data: {
    vsop87Bearth: unknown;
    vsop87Bmercury: unknown;
    vsop87Bvenus: unknown;
    vsop87Bmars: unknown;
    vsop87Bjupiter: unknown;
    vsop87Bsaturn: unknown;
  };
  export default data;
}
