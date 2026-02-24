export type YinYang = "Yang" | "Yin";
export type Element = "Wood" | "Fire" | "Earth" | "Metal" | "Water";

export type StemInfo = {
    char: string;
    element: Element;
    yinYang: YinYang;
    elementEmoji: string;
    yinYangEmoji: string;
};
export type BranchAnimal =
    | "Rat"
    | "Ox"
    | "Tiger"
    | "Rabbit"
    | "Dragon"
    | "Snake"
    | "Horse"
    | "Goat"
    | "Monkey"
    | "Rooster"
    | "Dog"
    | "Pig";

export type BranchInfo = {
    char: string;
    animal: BranchAnimal;
    element: Element;
    yinYang: YinYang;
    elementEmoji: string;
    yinYangEmoji: string;
    animalEmoji: string;
};

export const ELEMENT_EMOJI: Record<Element, string> = {
    Wood: "🌳",
    Fire: "🔥",
    Earth: "⛰️",
    Metal: "⚔️",
    Water: "🌊",
};

export const YINYANG_EMOJI: Record<YinYang, string> = {
    Yang: "☀️",
    Yin: "🌙",
};

export const ANIMAL_EMOJI: Record<BranchAnimal, string> = {
    Rat: "🐀",
    Ox: "🐂",
    Tiger: "🐅",
    Rabbit: "🐇",
    Dragon: "🐉",
    Snake: "🐍",
    Horse: "🐎",
    Goat: "🐐",
    Monkey: "🐒",
    Rooster: "🐓",
    Dog: "🐕",
    Pig: "🐖",
};

const STEMS: Record<string, Omit<StemInfo, "char">> = {
    "甲": { element: "Wood", yinYang: "Yang", elementEmoji: ELEMENT_EMOJI.Wood, yinYangEmoji: YINYANG_EMOJI.Yang },
    "乙": { element: "Wood", yinYang: "Yin", elementEmoji: ELEMENT_EMOJI.Wood, yinYangEmoji: YINYANG_EMOJI.Yin },
    "丙": { element: "Fire", yinYang: "Yang", elementEmoji: ELEMENT_EMOJI.Fire, yinYangEmoji: YINYANG_EMOJI.Yang },
    "丁": { element: "Fire", yinYang: "Yin", elementEmoji: ELEMENT_EMOJI.Fire, yinYangEmoji: YINYANG_EMOJI.Yin },
    "戊": { element: "Earth", yinYang: "Yang", elementEmoji: ELEMENT_EMOJI.Earth, yinYangEmoji: YINYANG_EMOJI.Yang },
    "己": { element: "Earth", yinYang: "Yin", elementEmoji: ELEMENT_EMOJI.Earth, yinYangEmoji: YINYANG_EMOJI.Yin },
    "庚": { element: "Metal", yinYang: "Yang", elementEmoji: ELEMENT_EMOJI.Metal, yinYangEmoji: YINYANG_EMOJI.Yang },
    "辛": { element: "Metal", yinYang: "Yin", elementEmoji: ELEMENT_EMOJI.Metal, yinYangEmoji: YINYANG_EMOJI.Yin },
    "壬": { element: "Water", yinYang: "Yang", elementEmoji: ELEMENT_EMOJI.Water, yinYangEmoji: YINYANG_EMOJI.Yang },
    "癸": { element: "Water", yinYang: "Yin", elementEmoji: ELEMENT_EMOJI.Water, yinYangEmoji: YINYANG_EMOJI.Yin },
};

const BRANCHES: Record<string, Omit<BranchInfo, "char">> = {
    "子": {
        animal: "Rat",
        element: "Water",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Water,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Rat,
    },
    "丑": {
        animal: "Ox",
        element: "Earth",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Earth,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Ox,
    },
    "寅": {
        animal: "Tiger",
        element: "Wood",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Wood,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Tiger,
    },
    "卯": {
        animal: "Rabbit",
        element: "Wood",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Wood,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Rabbit,
    },
    "辰": {
        animal: "Dragon",
        element: "Earth",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Earth,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Dragon,
    },
    "巳": {
        animal: "Snake",
        element: "Fire",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Fire,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Snake,
    },
    "午": {
        animal: "Horse",
        element: "Fire",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Fire,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Horse,
    },
    "未": {
        animal: "Goat",
        element: "Earth",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Earth,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Goat,
    },
    "申": {
        animal: "Monkey",
        element: "Metal",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Metal,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Monkey,
    },
    "酉": {
        animal: "Rooster",
        element: "Metal",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Metal,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Rooster,
    },
    "戌": {
        animal: "Dog",
        element: "Earth",
        yinYang: "Yang",
        elementEmoji: ELEMENT_EMOJI.Earth,
        yinYangEmoji: YINYANG_EMOJI.Yang,
        animalEmoji: ANIMAL_EMOJI.Dog,
    },
    "亥": {
        animal: "Pig",
        element: "Water",
        yinYang: "Yin",
        elementEmoji: ELEMENT_EMOJI.Water,
        yinYangEmoji: YINYANG_EMOJI.Yin,
        animalEmoji: ANIMAL_EMOJI.Pig,
    },
};

export function getStemInfo(stemChar: string): StemInfo | null {
    const s = STEMS[stemChar];
    return s ? { char: stemChar, ...s } : null;
}

export function getBranchInfo(branchChar: string): BranchInfo | null {
    const b = BRANCHES[branchChar];
    return b ? { char: branchChar, ...b } : null;
}

export function parseGanZhi(gz: string | null | undefined): { stem: StemInfo | null; branch: BranchInfo | null } {
    if (!gz || gz.length < 2) return { stem: null, branch: null };
    const stemChar = gz[0];
    const branchChar = gz[1];

    if (!stemChar || !branchChar) return { stem: null, branch: null };

    return {
        stem: getStemInfo(stemChar),
        branch: getBranchInfo(branchChar),
    };
}

export function formatStemDisplay(gan: string | null | undefined): string {
    if (!gan) return "";
    const info = getStemInfo(gan);
    if (!info) return gan;
    return `${info.char} ${info.element} ${info.yinYang} ${info.elementEmoji}${info.yinYangEmoji}`;
}

export function formatBranchDisplay(zhi: string | null | undefined): string {
    if (!zhi) return "";
    const info = getBranchInfo(zhi);
    if (!info) return zhi;
    return `${info.char} ${info.animal} (${info.element} ${info.yinYang}) ${info.animalEmoji}(${info.elementEmoji}${info.yinYangEmoji})`;
}

export function formatGanZhiDisplay(gz: string | null | undefined): string {
    if (!gz || gz.length < 2) return gz ?? "";
    const info = parseGanZhi(gz);
    if (!info.stem || !info.branch) return gz;
    return `${info.stem.char}${info.branch.char} ${info.stem.element} ${info.stem.yinYang} ${info.branch.animal} ${info.stem.elementEmoji}${info.stem.yinYangEmoji}${info.branch.animalEmoji}`;
}