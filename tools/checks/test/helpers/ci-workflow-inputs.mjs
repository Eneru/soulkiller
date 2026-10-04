export function workflowEnvironment(definitions, context) {
  const values = new Map([
    ['${{ github.event_name }}', context.eventName],
    ['${{ github.event.pull_request.base.ref }}', context.baseRef ?? ''],
    ['${{ github.ref }}', context.ref],
    ['${{ github.ref_type }}', context.refType],
    ['${{ github.event.deleted || false }}', String(context.deleted ?? false)],
    ['${{ github.event.pull_request.base.sha || github.event.before }}', context.baseSha ?? ''],
  ]);
  return Object.fromEntries(Object.entries(definitions ?? {}).map(([name, expression]) => {
    if (!values.has(expression)) throw new Error('Unsupported synthetic workflow expression');
    return [name, values.get(expression)];
  }));
}

export function isSubscribed(workflow, context) {
  if (context.eventName === 'pull_request') return workflow.on.pull_request.branches.includes(context.baseRef);
  if (context.eventName !== 'push' || context.refType !== 'tag') return false;
  return workflow.on.push.tags.some((glob) => {
    const pattern = glob.replaceAll('.', '\\.').replaceAll('*', '.*');
    // eslint-disable-next-line security/detect-non-literal-regexp -- Pattern comes only from the parsed repository workflow, not from synthetic event input.
    return new RegExp('^' + pattern + '(?![\\s\\S])').test(context.ref.slice('refs/tags/'.length));
  });
}

export function isSelected(condition, eligible) {
  if (condition !== "steps.eligibility.outputs.eligible == 'true'") throw new Error('Heavy step lost its eligibility condition');
  return eligible === 'true';
}
