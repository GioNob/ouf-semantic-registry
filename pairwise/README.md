# Pairwise verification

This directory is the controlled entry point for future real 1+1 module tests.
The workflow intentionally refuses to report success until a versioned fixture
set and its peer adapter have been committed under `pairwise/fixtures/`.

Inputs are restricted to immutable/explicit image references and simple fixture
names. No workflow input is evaluated as a shell command.

