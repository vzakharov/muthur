import {
  boardComments,
  mountBoard,
} from "#src/review-board/pages/board/index.ts";
import { ROOT_ID } from "#src/review-board/shared/lib/page-ids.ts";
import "../styles/board.css";

const root = document.getElementById(ROOT_ID);
if (root === null) throw new Error(`the page has no #${ROOT_ID}`);
const comments = boardComments();
const board = mountBoard(root, { comments: comments.hook });
// A rejection here is not a designed absence: it surfaces as unhandled.
void comments.connect(board);
