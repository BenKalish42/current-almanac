export type TraditionType = 'loshu' | 'mewa' | 'ninestarki';

export interface PalaceSynthesis {
  loshu: string;
  mewa: string;
  ninestarki: string;
}

export interface NinePalaceData {
  number: number;
  loshuLabel: string;
  mewaLabel: string;
  nineStarLabel: string;
  loshuTextClass: string;
  mewaTextClass: string;
  nineStarTextClass: string;
  mewaBgClass: string;
  synthesisText: PalaceSynthesis;
}

export const ninePalacesDictionary: Record<number, NinePalaceData> = {
  1: {
    number: 1,
    loshuLabel: 'Water',
    mewaLabel: 'White',
    nineStarLabel: 'White Water',
    loshuTextClass: 'text-blue-600',
    mewaTextClass: 'text-slate-400',
    nineStarTextClass: 'text-blue-600',
    mewaBgClass: 'bg-slate-50 text-slate-800 border-slate-200',
    synthesisText: {
      loshu: 'Associated with Kan (Water) in the North. It represents the profound depths, danger, and the hidden potential of winter. It relates to wisdom, adaptability, and the kidneys.',
      mewa: 'White Mewa indicates a connection to spiritual purity, mental clarity, and the ancestors. It represents a mirror-like nature, reflecting truth.',
      ninestarki: '1 White Water relates to the beginning of the cycle, gestation, rest, and hidden deep emotions. It indicates a period of inner growth and planning.'
    }
  },
  2: {
    number: 2,
    loshuLabel: 'Earth',
    mewaLabel: 'Black',
    nineStarLabel: 'Black Earth',
    loshuTextClass: 'text-amber-700',
    mewaTextClass: 'text-slate-900',
    nineStarTextClass: 'text-slate-900',
    mewaBgClass: 'bg-slate-800 text-slate-100 border-slate-700',
    synthesisText: {
      loshu: 'Associated with Kun (Earth) in the Southwest. It embodies receptive, nurturing, and maternal energy. It represents devotion, the stomach, and physical manifestation.',
      mewa: 'Black Mewa signifies karmic debts, intensity, and deep grounding. It represents a mysterious, transformative space that absorbs and recycles energy.',
      ninestarki: '2 Black Earth relates to nurturing, supporting others, slow steady progress, and the mother archetype. It is a time for preparation and attending to details.'
    }
  },
  3: {
    number: 3,
    loshuLabel: 'Wood',
    mewaLabel: 'Indigo',
    nineStarLabel: 'Jade Wood',
    loshuTextClass: 'text-emerald-600',
    mewaTextClass: 'text-indigo-600',
    nineStarTextClass: 'text-emerald-600',
    mewaBgClass: 'bg-indigo-100 text-indigo-900 border-indigo-200',
    synthesisText: {
      loshu: 'Associated with Zhen (Thunder) in the East. It is the energy of springtime, awakening, initiative, and sudden movement. It relates to the liver and decisive action.',
      mewa: 'Indigo Mewa points to a dynamic, restless, and quick-witted nature. It carries an independent and sometimes volatile spirit that seeks expansion.',
      ninestarki: '3 Jade Wood embodies youthful energy, new beginnings, rapid growth, and taking bold steps forward. It is highly active, sometimes impatient, and idealistic.'
    }
  },
  4: {
    number: 4,
    loshuLabel: 'Wood',
    mewaLabel: 'Green',
    nineStarLabel: 'Green Wood',
    loshuTextClass: 'text-emerald-600',
    mewaTextClass: 'text-emerald-600',
    nineStarTextClass: 'text-emerald-600',
    mewaBgClass: 'bg-emerald-100 text-emerald-900 border-emerald-200',
    synthesisText: {
      loshu: 'Associated with Xun (Wind) in the Southeast. It represents gentle penetration, flexibility, growth, and continuous spreading influence. Relates to the gallbladder.',
      mewa: 'Green Mewa represents elemental harmony, intelligence, and a balanced, communicative essence. It relates to the natural world and steady growth.',
      ninestarki: '4 Green Wood is about maturation, networking, building trust, and expanding influence far and wide. It represents harmony, travel, and successful communication.'
    }
  },
  5: {
    number: 5,
    loshuLabel: 'Earth',
    mewaLabel: 'Yellow',
    nineStarLabel: 'Yellow Earth',
    loshuTextClass: 'text-amber-700',
    mewaTextClass: 'text-amber-600',
    nineStarTextClass: 'text-amber-700',
    mewaBgClass: 'bg-amber-100 text-amber-900 border-amber-200',
    synthesisText: {
      loshu: 'The Center. It acts as the pivot and the grounding axis for all other palaces. It embodies ultimate stability, equilibrium, and the core essence of the Earth element.',
      mewa: 'Yellow Mewa is the central point of karmic return and authority. It acts as an anchor and a profound turning point, holding great transformative power.',
      ninestarki: '5 Yellow Earth is the center of the Taiji. It carries intense karmic weight, indicating massive shifts, destruction, and rebirth. It forces us to align with the core.'
    }
  },
  6: {
    number: 6,
    loshuLabel: 'Metal',
    mewaLabel: 'White',
    nineStarLabel: 'White Metal',
    loshuTextClass: 'text-slate-500',
    mewaTextClass: 'text-slate-400',
    nineStarTextClass: 'text-slate-500',
    mewaBgClass: 'bg-zinc-100 text-zinc-800 border-zinc-200',
    synthesisText: {
      loshu: 'Associated with Qian (Heaven) in the Northwest. It embodies creative power, authority, fatherhood, and unwavering strength. It relates to the lungs and the head.',
      mewa: 'White Mewa in this context points to divine authority, leadership, and a cool, calculating intellect. It represents high standards and discipline.',
      ninestarki: '6 White Metal brings themes of leadership, perfectionism, karma of the ancestors, and taking responsibility. It denotes a period of harvest and high status.'
    }
  },
  7: {
    number: 7,
    loshuLabel: 'Metal',
    mewaLabel: 'Red',
    nineStarLabel: 'Red Metal',
    loshuTextClass: 'text-slate-500',
    mewaTextClass: 'text-rose-600',
    nineStarTextClass: 'text-rose-600',
    mewaBgClass: 'bg-red-100 text-red-900 border-red-200',
    synthesisText: {
      loshu: 'Associated with Dui (Lake) in the West. It represents joy, communication, autumn, and the setting sun. It relates to the mouth and sharing ideas.',
      mewa: 'Red Mewa carries an energetic spark of passion, speech, and magnetism. It often denotes a charismatic, persuasive, and communicative nature.',
      ninestarki: '7 Red Metal is about joy, relaxation, socializing, and reaping rewards. It warns against overindulgence and encourages finding beauty and pleasure in life.'
    }
  },
  8: {
    number: 8,
    loshuLabel: 'Earth',
    mewaLabel: 'White',
    nineStarLabel: 'White Earth',
    loshuTextClass: 'text-amber-700',
    mewaTextClass: 'text-slate-400',
    nineStarTextClass: 'text-amber-700',
    mewaBgClass: 'bg-stone-100 text-stone-800 border-stone-200',
    synthesisText: {
      loshu: 'Associated with Gen (Mountain) in the Northeast. It symbolizes stillness, meditation, and the boundary between ending and beginning. Relates to the hands and quiet strength.',
      mewa: 'White Mewa here brings a calm, enduring spiritual quality. It signifies inner wealth, persistence, and a deeply grounded, contemplative state.',
      ninestarki: '8 White Earth signifies major transitions, mountains, stopping to evaluate, and periods of profound inner change. It is a time for reflection and redirection.'
    }
  },
  9: {
    number: 9,
    loshuLabel: 'Fire',
    mewaLabel: 'Red',
    nineStarLabel: 'Purple Fire',
    loshuTextClass: 'text-rose-600',
    mewaTextClass: 'text-rose-600',
    nineStarTextClass: 'text-purple-600',
    mewaBgClass: 'bg-rose-100 text-rose-900 border-rose-200',
    synthesisText: {
      loshu: 'Associated with Li (Fire) in the South. It embodies clarity, visibility, fame, and the height of summer. It relates to the heart and the eyes.',
      mewa: 'Red Mewa burns with ambition, visionary insight, and spiritual passion. It represents illumination, warmth, and the capacity to guide others.',
      ninestarki: '9 Purple Fire represents the peak of visibility, clarity, fame, and parting. It is a highly energetic phase where things come to light, demanding truth and separation.'
    }
  }
};

export function getPalaceStars(centerStar: number): Record<string, number> {
  const calc = (offset: number) => ((centerStar + offset - 1) % 9) + 1;
  return {
    Center: centerStar,
    NW: calc(1),
    W: calc(2),
    NE: calc(3),
    S: calc(4),
    N: calc(5),
    SW: calc(6),
    E: calc(7),
    SE: calc(8)
  };
}

export const gridLayoutDirections = [
  'SE', 'S', 'SW',
  'E', 'Center', 'W',
  'NE', 'N', 'NW'
] as const;
