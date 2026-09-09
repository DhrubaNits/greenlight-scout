import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getDecision,
  saveDecision,
} from "../api";

import type {
  AnalyzeResponse,
  DecisionType,
  ReviewItemType,
} from "../types";


// ============================================================
// TYPES
// ============================================================

type DecisionStatus =
  | "NOT_REVIEWED"
  | DecisionType;


interface DecisionPanelProps {
  result: AnalyzeResponse;
}


interface ReviewItem {
  id: string;
  type: ReviewItemType;
  title: string;
  category?: string;
}


// ============================================================
// HELPERS
// ============================================================

function formatCategory(
  category?: string
): string {

  if (!category) {
    return "";
  }

  return category
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


// ============================================================
// DECISION PANEL
// ============================================================

function DecisionPanel({
  result,
}: DecisionPanelProps) {

  // ----------------------------------------------------------
  // REVIEW STATE
  // ----------------------------------------------------------

  const [
    reviewedItems,
    setReviewedItems,
  ] = useState<
    Record<string, boolean>
  >({});


  // ----------------------------------------------------------
  // DECISION STATE
  // ----------------------------------------------------------

  const [
    selectedDecision,
    setSelectedDecision,
  ] = useState<DecisionStatus>(
    "NOT_REVIEWED"
  );


  const [
    savedDecision,
    setSavedDecision,
  ] = useState<DecisionStatus>(
    "NOT_REVIEWED"
  );


  // ----------------------------------------------------------
  // NOTES
  // ----------------------------------------------------------

  const [
    notes,
    setNotes,
  ] = useState("");


  const [
    savedNotes,
    setSavedNotes,
  ] = useState("");


  // ----------------------------------------------------------
  // API STATE
  // ----------------------------------------------------------

  const [
    loadingDecision,
    setLoadingDecision,
  ] = useState(false);


  const [
    saving,
    setSaving,
  ] = useState(false);


  const [
    saveError,
    setSaveError,
  ] = useState<string | null>(
    null
  );


  const [
    saveSuccess,
    setSaveSuccess,
  ] = useState(false);


  // ==========================================================
  // BUILD REVIEW ITEMS
  // ==========================================================

  const reviewItems =
    useMemo<ReviewItem[]>(() => {

      const confirmationItems =
        result.requires_confirmation.map(
          (claim): ReviewItem => ({
            id:
              `claim-${claim.claim_id}`,

            type:
              "CONFIRMATION",

            title:
              claim.statement,

            category:
              claim.category,
          })
        );


      const questionItems =
        result.open_questions.map(
          (
            question,
            index
          ): ReviewItem => ({
            id:
              `question-${index}`,

            type:
              "OPEN_QUESTION",

            title:
              question,
          })
        );


      return [
        ...confirmationItems,
        ...questionItems,
      ];

    }, [
      result.requires_confirmation,
      result.open_questions,
    ]);


  // ==========================================================
  // RESTORE SAVED HUMAN DECISION
  // ==========================================================

  useEffect(() => {

    let cancelled = false;


    async function restoreDecision() {

      setLoadingDecision(true);

      setSaveError(null);

      setSaveSuccess(false);

      setReviewedItems({});

      setSelectedDecision(
        "NOT_REVIEWED"
      );

      setSavedDecision(
        "NOT_REVIEWED"
      );

      setNotes("");

      setSavedNotes("");


      try {

        const saved =
          await getDecision(
            result.request_id
          );


        if (
          cancelled
          || !saved
        ) {
          return;
        }


        const restoredItems:
          Record<
            string,
            boolean
          > = {};


        saved.reviewed_items.forEach(
          (item) => {

            restoredItems[
              item.item_id
            ] = item.reviewed;

          }
        );


        setReviewedItems(
          restoredItems
        );


        setSelectedDecision(
          saved.decision
        );


        setSavedDecision(
          saved.decision
        );


        setNotes(
          saved.decision_notes
          ?? ""
        );


        setSavedNotes(
          saved.decision_notes
          ?? ""
        );

      } catch (error) {

        if (cancelled) {
          return;
        }


        console.error(
          "Unable to restore decision",
          error
        );


        setSaveError(
          error instanceof Error
            ? error.message
            : (
              "Unable to restore "
              + "saved decision."
            )
        );

      } finally {

        if (!cancelled) {

          setLoadingDecision(
            false
          );

        }

      }

    }


    restoreDecision();


    return () => {

      cancelled = true;

    };

  }, [
    result.request_id,
  ]);


  // ==========================================================
  // REVIEW METRICS
  // ==========================================================

  const reviewedCount =
    reviewItems.filter(
      (item) =>
        Boolean(
          reviewedItems[
            item.id
          ]
        )
    ).length;


  const unresolvedCount =
    reviewItems.length
    - reviewedCount;


  const allReviewed =
    reviewItems.length === 0
    || unresolvedCount === 0;


  // ==========================================================
  // REVIEW TOGGLE
  // ==========================================================

  function toggleReview(
    itemId: string
  ) {

    setReviewedItems(
      (current) => ({
        ...current,

        [itemId]:
          !current[
            itemId
          ],
      })
    );


    setSaveSuccess(
      false
    );

  }


  // ==========================================================
  // DECISION SELECT
  // ==========================================================

  function handleDecisionChange(
    decision: DecisionType
  ) {

    // Full Greenlight cannot be selected
    // until every review item is resolved.

    if (
      decision === "GREENLIGHT"
      && !allReviewed
    ) {
      return;
    }


    setSelectedDecision(
      decision
    );


    setSaveSuccess(
      false
    );

  }


  // ==========================================================
  // SAVE TO FASTAPI
  // ==========================================================

  async function handleSaveDecision() {

    if (
      selectedDecision
      === "NOT_REVIEWED"
    ) {
      return;
    }


    setSaving(true);

    setSaveError(null);

    setSaveSuccess(false);


    try {

      const items =
        reviewItems.map(
          (item) => ({
            item_id:
              item.id,

            item_type:
              item.type,

            title:
              item.title,

            reviewed:
              Boolean(
                reviewedItems[
                  item.id
                ]
              ),

            resolution:
              null,
          })
        );


      const saved =
        await saveDecision({

          analysis_id:
            result.request_id,

          decision:
            selectedDecision,

          decision_notes:
            notes.trim()
            || null,

          reviewer_name:
            null,

          reviewed_items:
            items,
        });


      setSelectedDecision(
        saved.decision
      );


      setSavedDecision(
        saved.decision
      );


      setNotes(
        saved.decision_notes
        ?? ""
      );


      setSavedNotes(
        saved.decision_notes
        ?? ""
      );


      const restoredItems:
        Record<
          string,
          boolean
        > = {};


      saved.reviewed_items.forEach(
        (item) => {

          restoredItems[
            item.item_id
          ] = item.reviewed;

        }
      );


      setReviewedItems(
        restoredItems
      );


      setSaveSuccess(
        true
      );

    } catch (error) {

      setSaveError(
        error instanceof Error
          ? error.message
          : (
            "Failed to save decision."
          )
      );

    } finally {

      setSaving(false);

    }

  }


  // ==========================================================
  // RESET UNSAVED CHANGES
  // ==========================================================

  async function handleReset() {

    setSaveError(null);

    setSaveSuccess(false);


    try {

      const saved =
        await getDecision(
          result.request_id
        );


      if (!saved) {

        setReviewedItems({});

        setSelectedDecision(
          "NOT_REVIEWED"
        );

        setSavedDecision(
          "NOT_REVIEWED"
        );

        setNotes("");

        setSavedNotes("");

        return;
      }


      const restoredItems:
        Record<
          string,
          boolean
        > = {};


      saved.reviewed_items.forEach(
        (item) => {

          restoredItems[
            item.item_id
          ] = item.reviewed;

        }
      );


      setReviewedItems(
        restoredItems
      );


      setSelectedDecision(
        saved.decision
      );


      setSavedDecision(
        saved.decision
      );


      setNotes(
        saved.decision_notes
        ?? ""
      );


      setSavedNotes(
        saved.decision_notes
        ?? ""
      );

    } catch (error) {

      setSaveError(
        error instanceof Error
          ? error.message
          : "Failed to reset."
      );

    }

  }


  // ==========================================================
  // WORKFLOW STATUS
  // ==========================================================

  const status =
    getWorkflowStatus(
      savedDecision,
      allReviewed
    );


  // ==========================================================
  // UI
  // ==========================================================

  return (
    <section className="decisionSection">

      <div className="decisionHeader">

        <div>

          <span className="stepLabel">
            HUMAN REVIEW
          </span>

          <h3>
            Production decision
          </h3>

          <p>
            Review unresolved evidence before
            recording a production decision.
          </p>

        </div>


        <div
          className={
            `decisionStatus ${status.className}`
          }
        >
          {status.label}
        </div>

      </div>


      {loadingDecision && (

        <div className="decisionLoading">
          Restoring saved human review...
        </div>

      )}


      <div className="decisionSummary">

        <div className="decisionMetric">

          <strong>
            {reviewItems.length}
          </strong>

          <span>
            Review items
          </span>

        </div>


        <div className="decisionMetric">

          <strong>
            {reviewedCount}
          </strong>

          <span>
            Reviewed
          </span>

        </div>


        <div className="decisionMetric">

          <strong>
            {unresolvedCount}
          </strong>

          <span>
            Outstanding
          </span>

        </div>

      </div>


      {reviewItems.length > 0 && (

        <div className="reviewBlock">

          <div className="reviewBlockHeading">

            <div>

              <h4>
                Outstanding review
              </h4>

              <p>
                Mark an item reviewed only after
                the production team has checked
                its applicability or confirmed it
                with the relevant authority.
              </p>

            </div>


            <span>
              {reviewedCount}
              {" / "}
              {reviewItems.length}
            </span>

          </div>


          <div className="reviewProgress">

            <div
              className="reviewProgressValue"
              style={{
                width:
                  reviewItems.length === 0
                    ? "100%"
                    : `${
                        Math.round(
                          (
                            reviewedCount
                            / reviewItems.length
                          )
                          * 100
                        )
                      }%`,
              }}
            />

          </div>


          <div className="reviewItemList">

            {reviewItems.map(
              (item) => {

                const reviewed =
                  Boolean(
                    reviewedItems[
                      item.id
                    ]
                  );


                return (
                  <label
                    className={
                      reviewed
                        ? "reviewItem reviewed"
                        : "reviewItem"
                    }
                    key={item.id}
                  >

                    <input
                      type="checkbox"
                      checked={reviewed}
                      onChange={() =>
                        toggleReview(
                          item.id
                        )
                      }
                    />


                    <span className="reviewCheckbox">
                      {reviewed
                        ? "✓"
                        : ""}
                    </span>


                    <span className="reviewItemContent">

                      <span className="reviewItemMeta">

                        {item.type
                          === "CONFIRMATION"
                          ? "NEEDS CONFIRMATION"
                          : "OPEN QUESTION"}

                        {item.category && (
                          <>
                            {" · "}
                            {formatCategory(
                              item.category
                            )}
                          </>
                        )}

                      </span>


                      <span className="reviewItemTitle">
                        {item.title}
                      </span>

                    </span>

                  </label>
                );

              }
            )}

          </div>

        </div>

      )}


      {reviewItems.length === 0 && (

        <div className="allClearNotice">

          <strong>
            No unresolved evidence items.
          </strong>

          <span>
            The analysis is ready for
            human production review.
          </span>

        </div>

      )}


      <div className="humanDecisionBlock">

        <div className="humanDecisionHeading">

          <h4>
            Human decision
          </h4>

          <p>
            This decision belongs to the
            production team, not the AI system.
          </p>

        </div>


        <div className="decisionOptions">

          <DecisionOption
            title="Greenlight"
            description={
              allReviewed
                ? (
                  "All identified review items "
                  + "have been reviewed."
                )
                : (
                  "Review all outstanding items "
                  + "before full Greenlight."
                )
            }
            selected={
              selectedDecision
              === "GREENLIGHT"
            }
            disabled={
              !allReviewed
            }
            onClick={() =>
              handleDecisionChange(
                "GREENLIGHT"
              )
            }
          />


          <DecisionOption
            title="Greenlight with conditions"
            description={
              "Proceed only with documented "
              + "conditions or unresolved items."
            }
            selected={
              selectedDecision
              ===
              "GREENLIGHT_WITH_CONDITIONS"
            }
            onClick={() =>
              handleDecisionChange(
                "GREENLIGHT_WITH_CONDITIONS"
              )
            }
          />


          <DecisionOption
            title="Do not greenlight"
            description={
              "Do not proceed with the scene "
              + "in its current production plan."
            }
            selected={
              selectedDecision
              === "DO_NOT_GREENLIGHT"
            }
            onClick={() =>
              handleDecisionChange(
                "DO_NOT_GREENLIGHT"
              )
            }
          />

        </div>


        <label className="decisionNotesLabel">

          Decision notes

          <textarea
            className="decisionNotes"
            rows={4}
            value={notes}
            onChange={(event) => {

              setNotes(
                event.target.value
              );

              setSaveSuccess(
                false
              );

            }}
            placeholder={
              "Add conditions, authority confirmations, "
              + "production notes, or reasons for the decision..."
            }
          />

        </label>


        <div className="decisionActions">

          <button
            className="saveDecisionButton"
            disabled={
              saving
              ||
              selectedDecision
              === "NOT_REVIEWED"
            }
            onClick={
              handleSaveDecision
            }
          >

            {saving
              ? "Saving..."
              : "Save Decision"}

          </button>


          <button
            className="resetDecisionButton"
            disabled={
              saving
            }
            onClick={
              handleReset
            }
          >
            Reset Changes
          </button>

        </div>


        {saveSuccess && (

          <div className="decisionSuccess">
            Decision persisted successfully.
          </div>

        )}


        {saveError && (

          <div className="errorBox">
            {saveError}
          </div>

        )}

      </div>


      {savedDecision
        !== "NOT_REVIEWED"
        && (

          <div className="savedDecisionCard">

            <div>

              <span>
                RECORDED DECISION
              </span>

              <strong>
                {
                  decisionLabel(
                    savedDecision
                  )
                }
              </strong>

            </div>


            {savedNotes && (

              <p>
                {savedNotes}
              </p>

            )}


            <small>
              Persisted to the Greenlight Scout
              decision record and audit history.
            </small>

          </div>

        )}


      <div className="decisionDisclaimer">

        Greenlight Scout supports
        pre-production research and decision
        preparation. A recorded Greenlight is a
        production workflow decision and does
        not constitute legal, regulatory,
        aviation, police, road-closure, or
        authority approval.

      </div>

    </section>
  );
}


// ============================================================
// DECISION OPTION
// ============================================================

interface DecisionOptionProps {
  title: string;
  description: string;
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
}


function DecisionOption({
  title,
  description,
  selected,
  disabled = false,
  onClick,
}: DecisionOptionProps) {

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={
        [
          "decisionOption",

          selected
            ? "selected"
            : "",

          disabled
            ? "disabled"
            : "",
        ]
          .filter(Boolean)
          .join(" ")
      }
    >

      <span className="decisionRadio">

        {selected
          ? "●"
          : "○"}

      </span>


      <span>

        <strong>
          {title}
        </strong>

        <small>
          {description}
        </small>

      </span>

    </button>
  );
}


// ============================================================
// DECISION LABEL
// ============================================================

function decisionLabel(
  decision: DecisionStatus
): string {

  switch (decision) {

    case "GREENLIGHT":
      return "Greenlight";

    case "GREENLIGHT_WITH_CONDITIONS":
      return "Greenlight with conditions";

    case "DO_NOT_GREENLIGHT":
      return "Do not greenlight";

    default:
      return "Not reviewed";
  }
}


// ============================================================
// WORKFLOW STATUS
// ============================================================

function getWorkflowStatus(
  decision: DecisionStatus,
  allReviewed: boolean
): {
  label: string;
  className: string;
} {

  if (
    decision === "GREENLIGHT"
  ) {

    return {
      label:
        "GREENLIGHT",

      className:
        "statusGreen",
    };

  }


  if (
    decision
    === "GREENLIGHT_WITH_CONDITIONS"
  ) {

    return {
      label:
        "GREENLIGHT WITH CONDITIONS",

      className:
        "statusConditional",
    };

  }


  if (
    decision
    === "DO_NOT_GREENLIGHT"
  ) {

    return {
      label:
        "DO NOT GREENLIGHT",

      className:
        "statusBlocked",
    };

  }


  if (allReviewed) {

    return {
      label:
        "READY FOR DECISION",

      className:
        "statusReady",
    };

  }


  return {
    label:
      "REVIEW REQUIRED",

    className:
      "statusReview",
  };
}


export default DecisionPanel;