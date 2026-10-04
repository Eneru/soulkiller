export function captureCliOutput() {
  const outputs = [];
  const errors = [];
  return {outputs, errors, io: {
    output: (value) => outputs.push(value),
    errorOutput: (value) => errors.push(value),
  }};
}
