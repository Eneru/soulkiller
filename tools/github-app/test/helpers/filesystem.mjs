import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile, symlink, rename, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

function checkFixturePath(file) {
  assert.equal(typeof file, 'string');
  const normalized = path.resolve(file);
  assert.ok(normalized.startsWith(path.join(os.tmpdir(), 'soulkiller-app-test-')));
  return normalized;
}

export async function fixtureWriteFile(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return writeFile(file, ...args);
}

export async function fixtureReadFile(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return readFile(file, ...args);
}

export async function fixtureMkdir(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return mkdir(file, ...args);
}

export async function fixtureSymlink(target, file, ...args) {
  checkFixturePath(file);
  if (path.isAbsolute(target)) checkFixturePath(target);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Destination and absolute target are confined to generated synthetic fixtures.
  return symlink(target, file, ...args);
}

export async function fixtureRename(from, to) {
  checkFixturePath(from);
  checkFixturePath(to);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Both paths belong to generated, container-internal synthetic fixtures.
  return rename(from, to);
}

export async function fixtureRm(file, options) {
  checkFixturePath(file);
  return rm(file, options);
}
