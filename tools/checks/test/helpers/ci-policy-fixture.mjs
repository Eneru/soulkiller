export function eventEnvironment(context) {
  return {
    SOULKILLER_CI_EVENT: context.eventName,
    SOULKILLER_CI_BASE: context.baseRef ?? '',
    SOULKILLER_CI_REF: context.ref,
    SOULKILLER_CI_REF_TYPE: context.refType,
    SOULKILLER_CI_DELETED: String(context.deleted),
  };
}

export function capturedOutput() {
  const lines = [];
  const errors = [];
  return { lines, errors, output: { log: (value) => lines.push(value), error: (value) => errors.push(value) } };
}
