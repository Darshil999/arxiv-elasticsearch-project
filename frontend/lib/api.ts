import { API_URL } from "./config";

export interface Paper {
  arxiv_id: string;
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  primary_category: string | null;
  published: string | null;
  updated: string | null;
  url: string;
  pdf_url: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  count: number;
  took_ms: number;
  results: Paper[];
}

export interface Stats {
  papers_indexed: number;
  embedding_model: string;
  embedding_dim: number;
}

export interface SearchParams {
  query: string;
  limit: number;
  categories?: string[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Free-tier backends sleep when idle and can take 1-2 minutes to wake up.
const REQUEST_TIMEOUT_MS = 150_000;

async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(REQUEST_TIMEOUT_MS);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, signal: combined });
  } catch (err) {
    if (signal?.aborted) throw err;
    if (timeout.aborted) throw new ApiError("The search server took too long to respond. Please try again.");
    throw new ApiError("Could not reach the search server. It may be starting up. Please try again in a moment.");
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) detail = body.detail[0].msg;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export function searchPapers(params: SearchParams, signal?: AbortSignal): Promise<SearchResponse> {
  return request<SearchResponse>(
    "/api/search",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: params.query,
        limit: params.limit,
        categories: params.categories?.length ? params.categories : undefined,
      }),
    },
    signal,
  );
}

export function getStats(signal?: AbortSignal): Promise<Stats> {
  return request<Stats>("/api/stats", undefined, signal);
}
