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
      loshu: 'Kan (Water), North. The configuration emphasizes depth, latency, and hidden potential. Associated with the kidneys; movement is downward and inward.',
      mewa: 'White Mewa. Reflective, cool clarity. The pattern reads as receptive and discerning rather than expressive.',
      ninestarki: '1 White Water. Beginning of a cycle: gestation, rest, low external output. Internal preparation dominates.'
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
      loshu: 'Kun (Earth), Southwest. Receptive, accumulative pattern. Associated with the stomach; movement absorbs and consolidates.',
      mewa: 'Black Mewa. High density, slow turnover. Energy is absorbed and recycled rather than expressed outward.',
      ninestarki: '2 Black Earth. Supporting role, slow steady progress, attention to details. External output is low; consolidation dominates.'
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
      loshu: 'Zhen (Thunder), East. Sudden, rising movement; awakening pattern. Associated with the liver; flow is upward and outward.',
      mewa: 'Indigo Mewa. Quick, restless dynamics. Friction tends to spike against constraints; flow is uneven.',
      ninestarki: '3 Jade Wood. Initiation, rapid expansion, low patience. Capacity drains quickly when momentum exceeds preparation.'
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
      loshu: 'Xun (Wind), Southeast. Gentle, persistent penetration; broad continuous spread. Associated with the gallbladder; flow is steady and lateral.',
      mewa: 'Green Mewa. Balanced, communicative pattern. Friction is low; signals propagate efficiently.',
      ninestarki: '4 Green Wood. Maturation, networking, expansion of influence. Capacity supports sustained outbound flow.'
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
      loshu: 'Center. Pivot and grounding axis. Equilibrium pattern; movement returns to baseline.',
      mewa: 'Yellow Mewa. Central return, anchor point. High inertia; small inputs produce large structural shifts.',
      ninestarki: '5 Yellow Earth. Center of the Taiji. Heavy turnover; existing structures dissolve and reform. Force applied here is amplified.'
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
      loshu: 'Qian (Heaven), Northwest. Creative authority, structural strength. Associated with the lungs and head; flow is precise and downward.',
      mewa: 'White Mewa. Cool, calculating pattern. High discipline; resistance to deviation is high.',
      ninestarki: '6 White Metal. Leadership, perfectionism, harvest. Capacity is high but rigid; flexibility is the limiting factor.'
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
      loshu: 'Dui (Lake), West. Outward expression, autumn descent. Associated with the mouth; flow is communicative and dispersive.',
      mewa: 'Red Mewa. Spark, magnetism, vocal expression. Energy releases outward; reservoirs deplete quickly.',
      ninestarki: '7 Red Metal. Socialization, relaxation, return on prior effort. Friction rises when pace exceeds reserves.'
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
      loshu: 'Gen (Mountain), Northeast. Stillness, boundary between ending and beginning. Associated with the hands; flow halts and re-orients.',
      mewa: 'White Mewa. Calm, enduring, grounded pattern. Resistance to motion is high; structural shifts are slow.',
      ninestarki: '8 White Earth. Major transitions, evaluation, redirection. External output is low; inward survey dominates.'
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
      loshu: 'Li (Fire), South. Clarity, visibility, peak of summer. Associated with the heart and eyes; flow is bright and outward.',
      mewa: 'Red Mewa. Illumination and warmth. Pattern reveals what was hidden; signals are amplified, friction is exposed.',
      ninestarki: '9 Purple Fire. Peak visibility, clarity, separation. Capacity peaks then declines; force applied at the peak yields the cleanest signal.'
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
