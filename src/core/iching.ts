// King Wen hexagram number -> 6-line binary string (TOP → BOTTOM)
// 1=yang (solid), 0=yin (broken). Source table: Wikibooks.  [oai_citation:1‡Wikibooks](https://en.wikibooks.org/wiki/I_Ching/The_64_Hexagrams)
export const HEX_BINARY_TOP_TO_BOTTOM: Record<number, string> = {
    1: "111111", 2: "000000", 3: "010001", 4: "100010", 5: "010111", 6: "111010",
    7: "000010", 8: "010000", 9: "110111", 10: "111011", 11: "000111", 12: "111000",
    13: "111101", 14: "101111", 15: "000100", 16: "001000", 17: "011001", 18: "100110",
    19: "000011", 20: "110000", 21: "101001", 22: "100101", 23: "100000", 24: "000001",
    25: "111001", 26: "100111", 27: "100001", 28: "011110", 29: "010010", 30: "101101",
    31: "011100", 32: "001110", 33: "111100", 34: "001111", 35: "101000", 36: "000101",
    37: "110101", 38: "101011", 39: "010100", 40: "001010", 41: "100011", 42: "110001",
    43: "011111", 44: "111110", 45: "011000", 46: "000110", 47: "011010", 48: "010110",
    49: "011101", 50: "101110", 51: "001001", 52: "100100", 53: "110100", 54: "001011",
    55: "001101", 56: "101100", 57: "110110", 58: "011011", 59: "110010", 60: "010011",
    61: "110011", 62: "001100", 63: "010101", 64: "101010",
};

const BINARY_TO_HEX: Record<string, number> = Object.fromEntries(
    Object.entries(HEX_BINARY_TOP_TO_BOTTOM).map(([k, v]) => [v, Number(k)])
);

export function getHexBinary(hex: number | null | undefined): string | null {
    if (!hex) return null;
    return HEX_BINARY_TOP_TO_BOTTOM[hex] ?? null;
}

export function getHexFromBinary(binary: string): number | null {
    if (!binary || binary.length !== 6) return null;
    return BINARY_TO_HEX[binary] ?? null;
}

/**
 * Flip bits at line positions (1–6) and return the relating (transformed) hexagram ID.
 * Line 1 = bottom (binary index 5), Line 6 = top (binary index 0). Binary is top→bottom.
 */
export function getRelatingHexagram(hexId: number | null, movingLines: number[]): number | null {
    const binary = getHexBinary(hexId);
    if (!binary || !movingLines.length) return hexId;
    const arr = [...binary];
    for (const lineNum of movingLines) {
        if (lineNum < 1 || lineNum > 6) continue;
        const idx = 6 - lineNum; // Line 1 → index 5 (bottom), Line 6 → index 0 (top)
        arr[idx] = arr[idx] === "1" ? "0" : "1";
    }
    return getHexFromBinary(arr.join("")) ?? hexId;
}
