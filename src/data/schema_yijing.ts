/**
 * Yi Jing (I Ching) Line Analysis Schema
 * Prepares the TypeScript interface for the massive Line Analysis data payload.
 * Each of the 64 hexagrams × 6 lines = 384 Yao entries will carry 6 philosophical analyses.
 *
 * @see docs/architecture/phase_2/Task11.7_HexagramPolish.md
 */

export interface YaoLineAnalysis {
  /** King Wen hexagram number (1–64) */
  hexagramId: number;
  /** Line position (1 = bottom, 6 = top) */
  lineNumber: number;
  /** Daoist (Liu Yiming / Wang Bi) interpretation */
  daoism: string;
  /** Confucian (Ten Wings) interpretation */
  confucianism: string;
  /** Buddhist (Chih-hsui Ou-i) interpretation */
  buddhism: string;
  /** Psychological (Jungian) interpretation */
  psychology: string;
  /** Human Design interpretation */
  humandesign: string;
  /** Gene Keys interpretation */
  genekeys: string;
}
