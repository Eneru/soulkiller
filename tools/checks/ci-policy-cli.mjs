import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isEligibleEvent } from './ci-policy.mjs';

export function main(args = [], environment = process.env, output = console) {
  if (args.length) {
    output.error('CI eligibility accepts environment inputs only.');
    return 1;
  }
  const eligible = isEligibleEvent({
    eventName: environment.SOULKILLER_CI_EVENT,
    baseRef: environment.SOULKILLER_CI_BASE,
    ref: environment.SOULKILLER_CI_REF,
    refType: environment.SOULKILLER_CI_REF_TYPE,
    deleted: environment.SOULKILLER_CI_DELETED === 'false' ? false : true,
  });
  output.log('eligible=' + eligible);
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
