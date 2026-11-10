/**
 * `eslint-plugin-boundaries` over the app graph: an import may reach its own
 * app or an ancestor, a strictly lower layer, through the target's public API.
 * Steiger checks one app root at a time, so this is the only checker that sees
 * an import cross apps.
 */

import type { ESLint } from "eslint";
import type { Config } from "eslint/config";
import boundariesPlugin from "eslint-plugin-boundaries";

import {
  ancestors,
  LAYERS,
  loadGraph,
  PUBLIC_API,
  SLICED_LAYERS,
  TEST_API,
  TEST_CODE,
  TEST_KIT,
} from "./masd-graph.ts";

const graph = loadGraph();
const APPS = [...graph.keys()];

// An app and everything it inherits: the apps its files may import from.
const reach = (app: string): string[] => [app, ...ancestors(graph, app)];

// `shared/lib` holds one sub-library per file instead of a segment-wide barrel,
// so a file there is its own public API — there is nothing beside it to hide.
// Entry stays at the top level: `*.ts` does not cross a slash, so anything a
// sub-library grows a directory for is internals again.
const sharedLibEntry = (apps: string[]) => ({
  type: "shared",
  captured: { appName: apps, segmentName: "lib" },
  fileInternalPath: "*.ts",
});

/** A file of the importing file's own slice, or of its own segment. */
const sibling = (layer: string) => ({
  type: layer,
  captured: SLICED_LAYERS.includes(layer)
    ? {
        appName: "{{ from.captured.appName }}",
        sliceName: "{{ from.captured.sliceName }}",
      }
    : {
        appName: "{{ from.captured.appName }}",
        segmentName: "{{ from.captured.segmentName }}",
      },
});

/**
 * `type`'s files in `app` entering `targets` through a public API, and their
 * test code through the test-only entry as well.
 */
const throughApi = (type: string, app: string, targets: object) => [
  {
    from: { element: { type, captured: { appName: app } } },
    allow: { to: { element: { ...targets, fileInternalPath: PUBLIC_API } } },
  },
  {
    from: {
      element: {
        type,
        captured: { appName: app },
        fileInternalPath: TEST_CODE,
      },
    },
    allow: { to: { element: { ...targets, fileInternalPath: TEST_API } } },
  },
];

const policiesFor = (app: string) => {
  const apps = reach(app);
  return [
    // `app` and `shared` are segmented rather than sliced, so a descendant's
    // overlays its ancestors' as one unit — a root layout composing the one
    // it extends, a shared segment building on its ancestor's — and their
    // files reach each other directly.
    ...["app", "shared"].map((layer) => ({
      from: { element: { type: layer, captured: { appName: app } } },
      allow: { to: { element: { type: layer, captured: { appName: apps } } } },
    })),
    // The app layer sits above every other, so it may enter any.
    {
      from: { element: { type: "app", captured: { appName: app } } },
      allow: {
        to: {
          element: {
            types: { anyOf: [...SLICED_LAYERS, "shared"] },
            captured: { appName: apps },
            fileInternalPath: PUBLIC_API,
          },
        },
      },
    },
    {
      from: {
        element: {
          types: { anyOf: ["app", ...SLICED_LAYERS] },
          captured: { appName: app },
        },
      },
      allow: { to: { element: sharedLibEntry(apps) } },
    },
    // Scripts have no public API, so an app's scripts enter its own and its
    // ancestors' directly; every layer, their own app's included, through one.
    {
      from: { element: { type: "script", captured: { appName: app } } },
      allow: {
        to: [
          { element: { type: "script", captured: { appName: apps } } },
          { element: sharedLibEntry(apps) },
        ],
      },
    },
    ...throughApi("script", app, {
      types: { anyOf: LAYERS },
      captured: { appName: apps },
    }),
    // Strictly downward: the same layer in an ancestor is as sideways as a
    // sibling slice.
    ...SLICED_LAYERS.flatMap((layer, index) =>
      throughApi(layer, app, {
        types: { anyOf: [...SLICED_LAYERS.slice(index + 1), "shared"] },
        captured: { appName: apps },
      }),
    ),
  ];
};

// The package's declarations say `export default`, while its CommonJS build
// assigns the plugin to `module.exports`; under NodeNext the types describe a
// wrapper object the runtime never hands out.
const boundaries = boundariesPlugin as unknown as ESLint.Plugin;

export const boundariesConfig: Config = {
  plugins: { boundaries },
  files: ["src/**/*.{ts,tsx}"],
  settings: {
    // Resolves the `#src/` alias (package.json `imports`) to the files it names.
    "import/resolver": {
      typescript: { project: "./tsconfig.json" },
    },
    "boundaries/elements": [
      // An app's own tooling, beside its layers rather than one of them.
      {
        type: "script",
        pattern: ["src/*/scripts"],
        capture: ["appName"],
        partialMatch: true,
      },
      ...["app", "shared"].map((layer) => ({
        type: layer,
        pattern: [`src/*/${layer}/*`],
        capture: ["appName", "segmentName"],
        partialMatch: true,
      })),
      ...SLICED_LAYERS.map((layer) => ({
        type: layer,
        pattern: [`src/*/${layer}/*`],
        capture: ["appName", "sliceName"],
        partialMatch: true,
      })),
    ],
    "boundaries/files": [
      { category: "test-kit", pattern: TEST_KIT },
      { category: "test", pattern: TEST_CODE },
    ],
  },
  rules: {
    "boundaries/dependencies": [
      "error",
      {
        default: "disallow",
        // A slice's files reaching each other are checked too, so a kit's
        // fence below holds inside its own slice.
        checkInternals: true,
        policies: [
          ...APPS.flatMap(policiesFor),
          // Inside its own slice, a file reaches any sibling directly.
          ...SLICED_LAYERS.map((layer) => ({
            from: { element: { type: layer } },
            allow: { to: { element: sibling(layer) } },
          })),
          // A kit is test code, which nothing shipped may load, so only the
          // test code of its own slice reaches it. Last, because the last
          // policy matching an import decides it.
          { disallow: { to: { file: { categories: "test-kit" } } } },
          ...LAYERS.map((layer) => ({
            from: { element: { type: layer, fileInternalPath: TEST_CODE } },
            allow: {
              to: {
                element: sibling(layer),
                file: { categories: "test-kit" },
              },
            },
          })),
        ],
      },
    ],
    "boundaries/no-ignored-dependencies": "error",
    "boundaries/no-unknown-dependencies": "error",
    "boundaries/no-unknown-files": "error",
  },
};
