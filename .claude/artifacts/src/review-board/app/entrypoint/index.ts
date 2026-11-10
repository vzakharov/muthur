import { mountBoard } from "#src/review-board/pages/board/index.ts";
import "../styles/board.css";

const root = document.getElementById("root");
if (root === null) throw new Error("the page has no #root");
mountBoard(root);
