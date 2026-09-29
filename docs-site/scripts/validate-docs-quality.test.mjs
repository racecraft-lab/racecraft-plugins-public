import assert from 'node:assert/strict';
import test from 'node:test';

import { DOCUMENTED_SAFETY_BOUNDARIES, validateSafetyBoundaries } from './validate-docs-quality.mjs';

const enforcerSource = (boundaries) =>
  Object.values(boundaries)
    .flatMap((group) => Object.values(group))
    .map((pattern) => `    ${pattern},`)
    .join('\n');

test('documented safety boundaries pass against the real validator', () => {
  const diagnostics = [];
  validateSafetyBoundaries(diagnostics);
  assert.deepEqual(diagnostics, []);
});

test('a documented boundary the validator no longer enforces fails', () => {
  const [group, entries] = Object.entries(DOCUMENTED_SAFETY_BOUNDARIES)[0];
  const [boundary, pattern] = Object.entries(entries)[0];
  const source = enforcerSource(DOCUMENTED_SAFETY_BOUNDARIES).replace(`${pattern},`, '');
  const diagnostics = [];
  validateSafetyBoundaries(diagnostics, { readEnforcerSource: () => source });
  assert.equal(diagnostics.length, 1);
  assert.match(diagnostics[0], new RegExp(`${group}.*${boundary}`));
});

test('an empty boundary group fails', () => {
  const diagnostics = [];
  validateSafetyBoundaries(diagnostics, { boundaries: { forbiddenInputs: {} }, readEnforcerSource: () => '' });
  assert.equal(diagnostics.length, 1);
});

test('an unreadable enforcer source fails instead of passing', () => {
  const diagnostics = [];
  validateSafetyBoundaries(diagnostics, {
    readEnforcerSource: () => {
      throw new Error('gone');
    },
  });
  assert.equal(diagnostics.length, 1);
});
