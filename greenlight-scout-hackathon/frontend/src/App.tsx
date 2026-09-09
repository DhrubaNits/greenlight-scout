import DecisionPanel from "./components/DecisionPanel";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import "./App.css";

import {
  analyzeScene,
  getSavedAnalysis,
} from "./api";

import type {
  AnalyzeResponse,
  Claim,
  Source,
} from "./types";


// ============================================================
// DEFAULT DATA
// ============================================================

const DEFAULT_REQUIREMENTS = [
  "drone establishing shot",
  "temporary road closure",
  "simulated police vehicle",
  "25 background actors",
];


// ============================================================
// HELPERS
// ============================================================

function formatCategory(
  category: string
) {
  return category
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


function authorityLabel(
  authority: string
) {
  return authority
    .replace("OFFICIAL_", "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


// ============================================================
// APP
// ============================================================

function App() {

  // ----------------------------------------------------------
  // INPUT STATE
  // ----------------------------------------------------------

  const [
    location,
    setLocation,
  ] = useState(
    "Central London"
  );


  const [
    sceneDescription,
    setSceneDescription,
  ] = useState(
    "Exterior night scene in Central London."
  );


  const [
    requirementsText,
    setRequirementsText,
  ] = useState(
    DEFAULT_REQUIREMENTS.join("\n")
  );


  // ----------------------------------------------------------
  // ANALYSIS STATE
  // ----------------------------------------------------------

  const [
    result,
    setResult,
  ] = useState<
    AnalyzeResponse | null
  >(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null
  );


  // ==========================================================
  // SOURCE LOOKUP MAP
  // ==========================================================

  const sourceMap =
    useMemo(() => {

      const map =
        new Map<
          string,
          Source
        >();


      result?.sources.forEach(
        (source) => {

          map.set(
            source.source_id,
            source
          );

        }
      );


      return map;

    }, [result]);


  // ==========================================================
  // RESTORE LAST SAVED ANALYSIS
  // ==========================================================

  useEffect(() => {

    let cancelled = false;


    async function restoreAnalysis() {

      const analysisId =
        localStorage.getItem(
          "greenlight-last-analysis-id"
        );


      if (!analysisId) {
        return;
      }


      try {

        const saved =
          await getSavedAnalysis(
            analysisId
          );


        if (cancelled) {
          return;
        }


        // Restore original scene input.

        setLocation(
          saved.location
        );


        setSceneDescription(
          saved.scene_description
        );


        setRequirementsText(
          saved.requirements.join(
            "\n"
          )
        );


        // Restore complete analysis.

        setResult(
          saved.analysis
        );

      } catch (err) {

        console.error(
          "Unable to restore saved analysis",
          err
        );


        localStorage.removeItem(
          "greenlight-last-analysis-id"
        );

      }

    }


    restoreAnalysis();


    return () => {

      cancelled = true;

    };

  }, []);


  // ==========================================================
  // ANALYZE
  // ==========================================================

  async function handleAnalyze() {

    setError(null);

    setResult(null);

    setLoading(true);


    try {

      const requirements =
        requirementsText
          .split("\n")
          .map(
            (item) =>
              item.trim()
          )
          .filter(Boolean);


      const response =
        await analyzeScene({

          location:
            location.trim(),

          scene_description:
            sceneDescription.trim(),

          requirements,

        });


      setResult(
        response
      );


      localStorage.setItem(
        "greenlight-last-analysis-id",
        response.request_id
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Analysis failed."
      );

    } finally {

      setLoading(false);

    }

  }


  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="app">

      {/* ======================================================
          TOP BAR
          ====================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brandMark">
            GS
          </div>


          <div>

            <div className="brandName">
              Greenlight Scout
            </div>

            <div className="brandSubtitle">
              Evidence-first pre-production intelligence
            </div>

          </div>

        </div>


        <div className="technologyBadge">
          Gemini + Parallel
        </div>

      </header>


      {/* ======================================================
          PAGE
          ====================================================== */}

      <main className="page">

        {/* ====================================================
            HERO
            ==================================================== */}

        <section className="hero">

          <div>

            <div className="eyebrow">
              PRE-PRODUCTION INTELLIGENCE
            </div>


            <h1>
              Know what needs clearance
              <span>
                {" "}
                before the cameras roll.
              </span>
            </h1>


            <p>
              Greenlight Scout analyzes a proposed
              scene, researches current filming
              requirements, verifies claims against
              authoritative sources, and separates
              confirmed evidence from items that still
              require human confirmation.
            </p>

          </div>

        </section>


        {/* ====================================================
            WORKSPACE
            ==================================================== */}

        <section className="workspace">

          {/* ==================================================
              INPUT
              ================================================== */}

          <div className="inputPanel">

            <div className="panelHeading">

              <div>

                <span className="stepLabel">
                  SCENE INPUT
                </span>

                <h2>
                  Production scenario
                </h2>

              </div>

            </div>


            <label>

              Filming location

              <input
                value={location}
                onChange={
                  (event) =>
                    setLocation(
                      event.target.value
                    )
                }
                placeholder="e.g. Central London"
              />

            </label>


            <label>

              Scene description

              <textarea
                rows={5}
                value={
                  sceneDescription
                }
                onChange={
                  (event) =>
                    setSceneDescription(
                      event.target.value
                    )
                }
                placeholder={
                  "Describe the proposed scene..."
                }
              />

            </label>


            <label>

              Production requirements

              <textarea
                rows={8}
                value={
                  requirementsText
                }
                onChange={
                  (event) =>
                    setRequirementsText(
                      event.target.value
                    )
                }
                placeholder={
                  "One requirement per line"
                }
              />


              <span className="fieldHint">
                Enter one production requirement
                per line.
              </span>

            </label>


            <button
              className="analyzeButton"
              onClick={
                handleAnalyze
              }
              disabled={
                loading
                || !location.trim()
                || !sceneDescription.trim()
              }
            >

              {loading
                ? "Researching & verifying..."
                : "Analyze Scene"}

            </button>


            {error && (

              <div className="errorBox">
                {error}
              </div>

            )}

          </div>


          {/* ==================================================
              RESULT
              ================================================== */}

          <div className="resultPanel">

            {!result
              && !loading
              && (

                <div className="emptyState">

                  <div className="emptyIcon">
                    ◎
                  </div>


                  <h3>
                    Production intelligence
                    will appear here
                  </h3>


                  <p>
                    Submit a scene to start the
                    Gemini + Parallel evidence
                    workflow.
                  </p>


                  <div className="workflowPreview">

                    <span>
                      Scene analysis
                    </span>

                    <strong>
                      →
                    </strong>

                    <span>
                      Web research
                    </span>

                    <strong>
                      →
                    </strong>

                    <span>
                      Evidence verification
                    </span>

                  </div>

                </div>

              )}


            {loading && (

              <div className="loadingState">

                <div className="loader" />


                <h3>
                  Researching the scene
                </h3>


                <p>
                  Gemini is orchestrating the
                  workflow while Parallel retrieves
                  current web evidence.
                </p>


                <div className="loadingSteps">

                  <span>
                    Scene requirements
                  </span>

                  <span>
                    Parallel web research
                  </span>

                  <span>
                    Claim verification
                  </span>

                  <span>
                    Semantic evidence gate
                  </span>

                </div>

              </div>

            )}


            {result && (

              <AnalysisResult
                result={result}
                sourceMap={sourceMap}
              />

            )}

          </div>

        </section>

      </main>

    </div>
  );
}


// ============================================================
// ANALYSIS RESULT
// ============================================================

interface AnalysisResultProps {

  result: AnalyzeResponse;

  sourceMap:
    Map<
      string,
      Source
    >;
}


function AnalysisResult({
  result,
  sourceMap,
}: AnalysisResultProps) {

  const verified =
    result.metrics.final_verified;


  const confirmation =
    result.metrics.requires_confirmation;


  const total =
    verified
    + confirmation;


  const readiness =
    total === 0
      ? 0
      : Math.round(
          (
            verified
            / total
          )
          * 100
        );


  return (
    <div className="analysisResult">

      {/* ======================================================
          RESULT HEADER
          ====================================================== */}

      <div className="resultHeader">

        <div>

          <span className="stepLabel">
            GREENLIGHT ASSESSMENT
          </span>


          <h2>
            {result.location}
          </h2>

        </div>


        <div className="requestBadge">
          Analysis complete
        </div>

      </div>


      {/* ======================================================
          SCENE FLAGS
          ====================================================== */}

      <div className="sceneFlags">

        <SceneFlag
          label="Night"
          active={
            result.scene_analysis
              .night_shoot
          }
        />


        <SceneFlag
          label="Drone"
          active={
            result.scene_analysis
              .drone_required
          }
        />


        <SceneFlag
          label="Road closure"
          active={
            result.scene_analysis
              .road_closure_required
          }
        />


        <SceneFlag
          label="Emergency vehicle"
          active={
            result.scene_analysis
              .emergency_vehicle
          }
        />


        <SceneFlag
          label="Crowd"
          active={
            result.scene_analysis
              .crowd_present
          }
        />

      </div>


      {/* ======================================================
          COVERAGE
          ====================================================== */}

      <div className="readinessCard">

        <div className="readinessTop">

          <div>

            <span>
              Evidence coverage
            </span>


            <strong>
              {readiness}%
            </strong>

          </div>


          <div className="metricSummary">

            <Metric
              value={
                verified
              }
              label="Verified"
            />


            <Metric
              value={
                confirmation
              }
              label="Need confirmation"
            />


            <Metric
              value={
                result
                  .open_questions
                  .length
              }
              label="Open questions"
            />

          </div>

        </div>


        <div className="progressTrack">

          <div
            className="progressValue"
            style={{
              width:
                `${readiness}%`,
            }}
          />

        </div>

      </div>


      {/* ======================================================
          HUMAN REVIEW
          ====================================================== */}

      <DecisionPanel
        result={result}
      />


      {/* ======================================================
          VERIFIED FINDINGS
          ====================================================== */}

      <section className="findingSection">

        <div className="sectionTitle verifiedTitle">

          <span className="statusIcon">
            ✓
          </span>


          <div>

            <h3>
              Verified findings
            </h3>


            <p>
              Directly supported by
              authoritative evidence.
            </p>

          </div>

        </div>


        <div className="findingList">

          {result
            .verified_findings
            .map(
              (claim) => (

                <ClaimCard
                  key={
                    claim.claim_id
                  }
                  claim={claim}
                  sourceMap={
                    sourceMap
                  }
                  verified
                />

              )
            )}

        </div>

      </section>


      {/* ======================================================
          REQUIRES CONFIRMATION
          ====================================================== */}

      <section className="findingSection">

        <div className="sectionTitle warningTitle">

          <span className="statusIcon">
            !
          </span>


          <div>

            <h3>
              Requires confirmation
            </h3>


            <p>
              Evidence is partial,
              secondary, or insufficient.
            </p>

          </div>

        </div>


        <div className="findingList">

          {result
            .requires_confirmation
            .map(
              (claim) => (

                <ClaimCard
                  key={
                    claim.claim_id
                  }
                  claim={claim}
                  sourceMap={
                    sourceMap
                  }
                />

              )
            )}

        </div>

      </section>


      {/* ======================================================
          OPEN QUESTIONS
          ====================================================== */}

      {result.open_questions.length
        > 0
        && (

          <section className="findingSection">

            <div className="sectionTitle">

              <span className="statusIcon">
                ?
              </span>


              <div>

                <h3>
                  Open questions
                </h3>


                <p>
                  Items the production team
                  should investigate further.
                </p>

              </div>

            </div>


            <div className="questionList">

              {result
                .open_questions
                .map(
                  (
                    question,
                    index
                  ) => (

                    <div
                      className="questionCard"
                      key={
                        `${question}-${index}`
                      }
                    >
                      {question}
                    </div>

                  )
                )}

            </div>

          </section>

        )}


      {/* ======================================================
          SOURCES
          ====================================================== */}

      <section className="sourceSection">

        <div className="sectionTitle">

          <span className="statusIcon">
            ↗
          </span>


          <div>

            <h3>
              Evidence sources
            </h3>


            <p>
              {
                result.metrics
                  .sources_retrieved
              }
              {" "}
              sources retrieved through
              Parallel Search.
            </p>

          </div>

        </div>


        <div className="sourceList">

          {result.sources.map(
            (source) => (

              <a
                key={
                  source.source_id
                }
                className="sourceCard"
                href={
                  source.url
                }
                target="_blank"
                rel="noreferrer"
              >

                <div>

                  <strong>
                    [{source.source_id}]
                    {" "}
                    {source.title}
                  </strong>


                  <span>
                    {
                      authorityLabel(
                        source
                          .authority_level
                      )
                    }
                  </span>

                </div>


                <span className="externalArrow">
                  ↗
                </span>

              </a>

            )
          )}

        </div>

      </section>

    </div>
  );
}


// ============================================================
// SCENE FLAG
// ============================================================

function SceneFlag({
  label,
  active,
}: {
  label: string;
  active: boolean;
}) {

  return (
    <div
      className={
        active
          ? "sceneFlag active"
          : "sceneFlag"
      }
    >

      <span>
        {active
          ? "✓"
          : "–"}
      </span>

      {label}

    </div>
  );
}


// ============================================================
// METRIC
// ============================================================

function Metric({
  value,
  label,
}: {
  value: number;
  label: string;
}) {

  return (
    <div className="metric">

      <strong>
        {value}
      </strong>


      <span>
        {label}
      </span>

    </div>
  );
}


// ============================================================
// CLAIM CARD
// ============================================================

function ClaimCard({
  claim,
  sourceMap,
  verified = false,
}: {
  claim: Claim;

  sourceMap:
    Map<
      string,
      Source
    >;

  verified?: boolean;
}) {

  return (
    <article
      className={
        verified
          ? "claimCard verifiedClaim"
          : "claimCard confirmationClaim"
      }
    >

      <div className="claimTop">

        <span className="claimCategory">
          {
            formatCategory(
              claim.category
            )
          }
        </span>


        {claim.support_level && (

          <span className="supportBadge">
            {
              claim.support_level
            }
          </span>

        )}

      </div>


      <p className="claimStatement">
        {claim.statement}
      </p>


      {claim.semantic_reason && (

        <p className="claimReason">
          {
            claim.semantic_reason
          }
        </p>

      )}


      <div className="claimSources">

        {claim.source_ids.map(
          (sourceId) => {

            const source =
              sourceMap.get(
                sourceId
              );


            if (!source) {

              return (
                <span
                  key={sourceId}
                >
                  [{sourceId}]
                </span>
              );

            }


            return (
              <a
                key={sourceId}
                href={
                  source.url
                }
                target="_blank"
                rel="noreferrer"
              >

                [{sourceId}]
                {" "}
                {source.title}

              </a>
            );

          }
        )}

      </div>

    </article>
  );
}


export default App;