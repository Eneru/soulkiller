import test from 'node:test';
import assert from 'node:assert/strict';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

for (const command of ['check', 'publish', 'verify']) {
  for (const [name, execute] of [['string', 'yes'], ['number', 1], ['object', {}]]) {
    test(command + ' rejects a truthy nonboolean ' + name + ' before local or remote work', async (t) => {
      // Arrange
      const f = await createPublicationFixture(t);
      const touched = [];
      f.workspace.snapshot = async () => { touched.push('snapshot'); throw new Error('unexpected snapshot'); };
      f.files.readBody = async () => { touched.push('body'); throw new Error('unexpected body read'); };
      f.publisher.auth.withInstallation = async () => { touched.push('authentication'); throw new Error('unexpected authentication'); };
      // Act
      const attempt = command === 'check' ? f.publisher.check({execute})
        : command === 'verify' ? f.publisher.verify({number: 17, execute})
          : f.publisher.publish({...publication, execute});
      // Assert
      await assert.rejects(attempt, code('BAD_ARGUMENT'));
      assert.deepEqual(touched, []);
      assert.equal(f.api.requests.length, 0);
      assert.equal(f.calls.length, 0);
    });
  }
}
