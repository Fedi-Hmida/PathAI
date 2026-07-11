import {
  Boxes,
  BookOpen,
  Braces,
  Brain,
  Circle,
  Code,
  Database,
  GitBranch,
  Layers,
  Network,
  Ruler,
  Scissors,
  Search,
  Sigma,
  Sparkles,
  Table,
  TrendingDown,
  type LucideIcon,
} from "lucide-react";

import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

// Concept IDs are arbitrary slugs, so there is no reliable 1:1 icon mapping.
// This is a deterministic keyword heuristic over the label + id, purely
// decorative, that lights up themed icons for common concepts and falls back
// to a neutral glyph otherwise — first match in this ordered list wins.
const KEYWORD_ICONS: ReadonlyArray<[RegExp, LucideIcon]> = [
  [/vector|embed/, Boxes],
  [/chunk/, Scissors],
  [/retriev|search|index/, Search],
  [/eval|metric|recall|precision|score/, Ruler],
  [/rerank|rank/, TrendingDown],
  [/gradient|optim|descent/, TrendingDown],
  [/probab|statis|bayes/, Sigma],
  [/rag|fundamental|foundation|intro|basic/, BookOpen],
  [/api|endpoint|service|backend/, Braces],
  [/data|pandas|table|dataframe/, Table],
  [/database|sql|store|storage/, Database],
  [/algebra|matrix|linear|math/, Sigma],
  [/model|neural|network|deep|learn/, Brain],
  [/graph|node|tree|dag/, Network],
  [/system|architect|design|pipeline/, Layers],
  [/recommend|personal|rank/, Sparkles],
  [/code|program|python|script/, Code],
  [/branch|version|git|flow/, GitBranch],
];

export function iconForConcept(concept: ConceptMasteryDTO): LucideIcon {
  const haystack = `${concept.label} ${concept.concept_id}`.toLowerCase();
  for (const [pattern, icon] of KEYWORD_ICONS) {
    if (pattern.test(haystack)) {
      return icon;
    }
  }
  return Circle;
}
