import {
  boardComments,
  mountBoard,
} from "#src/review-board/pages/board/index.ts";
import "../styles/board.css";

const root = document.getElementById("root");
if (root === null) throw new Error("the page has no #root");
const comments = boardComments();
const board = mountBoard(root, { comments: comments.hook });
// A rejection here is not a designed absence: it surfaces as unhandled.
void comments.connect(board);
