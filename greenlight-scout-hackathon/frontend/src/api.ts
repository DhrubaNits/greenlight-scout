import type {
  AnalyzeRequest,
  AnalyzeResponse,
  DecisionHistoryItem,
  DecisionRequest,
  DecisionResponse,
  SavedAnalysisResponse,
} from "./types";


// ============================================================
// API BASE URL
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


// ============================================================
// COMMON ERROR HANDLING
// ============================================================

async function getErrorMessage(
  response: Response,
  fallback: string
): Promise<string> {

  try {

    const body =
      await response.json();

    if (body?.detail) {
      return body.detail;
    }

  } catch {
    // Use fallback.
  }

  return fallback;
}


// ============================================================
// ANALYZE SCENE
// ============================================================

export async function analyzeScene(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analyze`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(
          request
        ),
    }
  );


  if (!response.ok) {

    const message =
      await getErrorMessage(
        response,
        `Analysis failed with status ${response.status}`
      );

    throw new Error(
      message
    );
  }


  return response.json();
}


// ============================================================
// GET SAVED ANALYSIS
// ============================================================

export async function getSavedAnalysis(
  analysisId: string
): Promise<SavedAnalysisResponse> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analyses/${analysisId}`
  );


  if (!response.ok) {

    const message =
      await getErrorMessage(
        response,
        "Failed to load saved analysis."
      );

    throw new Error(
      message
    );
  }


  return response.json();
}


// ============================================================
// SAVE HUMAN DECISION
// ============================================================

export async function saveDecision(
  request: DecisionRequest
): Promise<DecisionResponse> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/decisions`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(
          request
        ),
    }
  );


  if (!response.ok) {

    const message =
      await getErrorMessage(
        response,
        "Failed to save decision."
      );

    throw new Error(
      message
    );
  }


  return response.json();
}


// ============================================================
// GET CURRENT HUMAN DECISION
// ============================================================

export async function getDecision(
  analysisId: string
): Promise<
  DecisionResponse | null
> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/decisions/${analysisId}`
  );


  // No decision yet is a valid state.
  if (
    response.status === 404
  ) {
    return null;
  }


  if (!response.ok) {

    const message =
      await getErrorMessage(
        response,
        "Failed to load saved decision."
      );

    throw new Error(
      message
    );
  }


  return response.json();
}


// ============================================================
// GET DECISION HISTORY
// ============================================================

export async function getDecisionHistory(
  analysisId: string
): Promise<
  DecisionHistoryItem[]
> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/decisions/${analysisId}/history`
  );


  if (!response.ok) {

    const message =
      await getErrorMessage(
        response,
        "Failed to load decision history."
      );

    throw new Error(
      message
    );
  }


  return response.json();
}