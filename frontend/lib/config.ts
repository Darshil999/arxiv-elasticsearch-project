/** Public configuration. NEXT_PUBLIC_* values are inlined into the bundle at build time. */

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/** Optional link to the source repository, shown in the header. */
export const GITHUB_URL = process.env.NEXT_PUBLIC_GITHUB_URL || "";

export const RESULT_LIMITS = [5, 10, 20, 30, 50] as const;
export const DEFAULT_LIMIT = 10;

/** Categories offered as filters. Keep in sync with DEFAULT_CATEGORIES in scripts/common.py. */
export const CATEGORIES: { id: string; label: string }[] = [
  { id: "cs.AI", label: "Artificial Intelligence" },
  { id: "cs.CL", label: "Computation & Language" },
  { id: "cs.CV", label: "Computer Vision" },
  { id: "cs.LG", label: "Machine Learning" },
  { id: "cs.IR", label: "Information Retrieval" },
  { id: "cs.DC", label: "Distributed Computing" },
  { id: "cs.CR", label: "Security & Cryptography" },
  { id: "cs.RO", label: "Robotics" },
];

export const EXAMPLE_QUERIES = [
  "transformer models for computer vision",
  "making large language models reason step by step",
  "consensus protocols for distributed systems",
  "robots learning to grasp objects",
  "detecting adversarial attacks on neural networks",
  "retrieval augmented generation",
];
