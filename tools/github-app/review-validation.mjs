import { API, BOT, REPOSITORY } from './constants.mjs';
import { ensure } from './guards.mjs';

export const PAGE_SIZE = 100;
export const MAX_PAGES = 10;
export const REPLY_METADATA = 'Reply to maintainer review';

export function positiveInteger(value) {
  return Number.isSafeInteger(value) && value > 0;
}

export function verifyCommentLocation(value, number) {
  ensure(positiveInteger(value?.id)
    && value.pull_request_url === API + '/repos/' + REPOSITORY + '/pulls/' + number
    && value.url === API + '/repos/' + REPOSITORY + '/pulls/comments/' + value.id
    && value.html_url === 'https://github.com/' + REPOSITORY + '/pull/' + number
      + '#discussion_r' + value.id, 'REVIEW_COMMENT_INVALID');
}

export function verifyTarget(value, number, comment) {
  verifyCommentLocation(value, number);
  ensure(value.id === comment && value.user?.login === 'Eneru'
    && (value.in_reply_to_id === undefined || value.in_reply_to_id === null), 'REVIEW_COMMENT_INVALID');
}

export function verifyReply(value, number, comment, text) {
  verifyCommentLocation(value, number);
  ensure(value.user?.login === BOT && value.in_reply_to_id === comment
    && value.body === text, 'REPLY_FAILED');
}
