import type { Plugin } from "esbuild";
import { compile } from "sass";

/** Compiles an imported `.scss` file with Dart Sass and hands esbuild the CSS. */
export const scss: Plugin = {
  name: "scss",
  setup(build) {
    build.onLoad({ filter: /\.scss$/ }, ({ path }) => ({
      contents: compile(path).css,
      loader: "css",
    }));
  },
};
