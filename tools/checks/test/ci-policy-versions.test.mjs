import assert from 'node:assert/strict';
import test from 'node:test';
import { isVersionTag } from '../ci-policy.mjs';

const validTags = [
  '0.0.0', '1.2.3', 'v1.2.3', '10.20.30', '999999999999999999999.2.3',
  '1.2.3-alpha', 'v1.2.3-alpha.1', '1.2.3-0', '1.2.3-x.7.z.92', '1.2.3--',
  '1.2.3-01a', '1.2.3-a01', '1.2.3-a-1', '1.2.3+001', 'v1.2.3+build.007',
  '1.2.3-alpha.1+sha.0123', '1.2.3+abc-123', '1.2.3+-',
];
const invalidTags = [
  '', 'v', 'V1.2.3', 'vv1.2.3', '1', '1.2', '1.2.3.4', '01.2.3', '1.02.3',
  '1.2.03', '1.2.3-', '1.2.3-alpha.', '1.2.3-.alpha', '1.2.3-alpha..beta',
  '1.2.3-00', '1.2.3-alpha.01', '1.2.3-0000000000000000000001', '1.2.3+',
  '1.2.3+build.', '1.2.3+.build', '1.2.3+build..sha', '1.2.3+a+b',
  ' 1.2.3', '1.2.3 ', '1.2.3\n', '1.2.3\r', '1.2.3\t', '1.2.3-ö',
  '1.2.3+_build', '1.2.3/release', '1.2.3;echo unsafe', '.1.2.3', '-1.2.3',
  undefined, null, 123, {}, [],
];

for (const tag of validTags) {
  test('accepts valid version tag ' + tag, () => {
    // Arrange
    const candidate = tag;
    // Act
    const eligible = isVersionTag(candidate);
    // Assert
    assert.equal(eligible, true);
  });
}
for (const [index, tag] of invalidTags.entries()) {
  test('rejects malformed version case ' + index + ': ' + JSON.stringify(tag), () => {
    // Arrange
    const candidate = tag;
    // Act
    const eligible = isVersionTag(candidate);
    // Assert
    assert.equal(eligible, false);
  });
}
