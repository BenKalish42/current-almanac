/**
 * Audit every synthesisText string in the Nine Palaces dictionary
 * against the Output Contract. Any drift here would surface to the
 * user the moment they click a palace.
 */
import { describe, it, expect } from "vitest";
import { ninePalacesDictionary } from "@/data/ninePalacesDictionary";
import { auditCompliance, formatViolations } from "@/contracts/outputContract";

describe("Nine Palaces dictionary — Output Contract", () => {
  for (let n = 1; n <= 9; n++) {
    const data = ninePalacesDictionary[n];
    if (!data) continue;
    for (const [tradition, text] of Object.entries(data.synthesisText)) {
      it(`palace ${n} / ${tradition} is contract-compliant`, () => {
        const audit = auditCompliance(text);
        if (!audit.ok) {
          // Useful failure message
          throw new Error(
            `Palace ${n}/${tradition}: violations: ${formatViolations(audit.violations)}\n  text: "${text}"`
          );
        }
        expect(audit.ok).toBe(true);
      });
    }
  }
});
