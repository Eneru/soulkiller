function isNumericIdentifier(value) {
  return /^(0|[1-9][0-9]*)$/.test(value);
}

function areIdentifiersValid(value, prerelease) {
  return value.split('.').every((identifier) => {
    if (!/^[0-9A-Za-z-]+$/.test(identifier)) return false;
    return !prerelease || !/^[0-9]+$/.test(identifier) || isNumericIdentifier(identifier);
  });
}

export function isVersionTag(tag) {
  if (typeof tag !== 'string' || !tag || /[^0-9A-Za-z.+-]/.test(tag)) return false;
  const version = tag.startsWith('v') ? tag.slice(1) : tag;
  const [main, build, ...extraBuild] = version.split('+');
  if (extraBuild.length || (build !== undefined && !areIdentifiersValid(build, false))) return false;
  const dash = main.indexOf('-');
  const core = dash === -1 ? main : main.slice(0, dash);
  const prerelease = dash === -1 ? undefined : main.slice(dash + 1);
  if (prerelease !== undefined && !areIdentifiersValid(prerelease, true)) return false;
  const numbers = core.split('.');
  return numbers.length === 3 && numbers.every(isNumericIdentifier);
}

export function isEligibleEvent(context) {
  if (!context || typeof context !== 'object' || context.deleted !== false) return false;
  const { eventName, baseRef, ref, refType } = context;
  if (typeof ref !== 'string') return false;
  if (eventName === 'pull_request') {
    return baseRef === 'main' && refType === 'branch' && /^refs\/pull\/[1-9][0-9]*\/merge(?![\s\S])/.test(ref);
  }
  return eventName === 'push' && refType === 'tag' && ref.startsWith('refs/tags/') &&
    isVersionTag(ref.slice('refs/tags/'.length));
}
