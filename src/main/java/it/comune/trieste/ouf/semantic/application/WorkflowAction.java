package it.comune.trieste.ouf.semantic.application;

/** Lifecycle actions advertised by Semantic. Every command still enforces its own authorization and preconditions. */
public enum WorkflowAction {
  POLL_DISCOVERY, LIST_CANDIDATES, ADOPT_CANDIDATE, PREPARE_REVIEW, REQUEST_APPROVAL,
  WAIT_HUMAN_DECISION, REVISE_PROPOSAL, NONE
}
