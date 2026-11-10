import * as parser from "@typescript-eslint/parser";
import { Linter } from "eslint";
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import rule from "./no-pick-omit.ts";

const linter = new Linter({ configType: "flat" });

function reports(code: string): string[] {
  return linter
    .verify(
      code,
      [
        {
          files: ["**/*.ts"],
          languageOptions: { parser },
          plugins: { masd: { rules: { "no-pick-omit": rule } } },
          rules: { "masd/no-pick-omit": "error" },
        },
      ],
      "fixture.ts",
    )
    .map(({ message, ruleId }) => {
      assert.equal(ruleId, "masd/no-pick-omit", message);
      return message;
    });
}

describe("no-pick-omit", () => {
  for (const [name, code] of [
    [
      "an in-file type",
      "type Leg = { from: string }; type A = Pick<Leg, 'from'>;",
    ],
    [
      "a relative import",
      "import type { Leg } from './flight'; type A = Pick<Leg, 'from'>;",
    ],
    [
      "a #src/ import",
      "import type { Leg } from '#src/app/x'; type A = Omit<Leg, 'from'>;",
    ],
    [
      "a namespace member",
      "import type * as F from './flight'; type A = Pick<F.Leg, 'to'>;",
    ],
    [
      "an indexed access",
      "type M = { a: { b: 1 } }; type A = Pick<M['a'], 'b'>;",
    ],
    [
      "typeof inside a library generic",
      "import * as z from 'zod'; const Runs = z.array(z.object({})); type A = Pick<z.infer<typeof Runs>[number], 'from'>;",
    ],
    [
      "a repo generic over a type parameter",
      "type Box<T> = { v: T }; function f<T>(b: Pick<Box<T>, 'v'>) { return b; }",
    ],
    [
      "an import() of a repo path",
      "type A = Pick<import('./flight').Leg, 'to'>;",
    ],
    [
      "a Pick nested in Partial",
      "type Leg = { from: string }; type A = Partial<Pick<Leg, 'from'>>;",
    ],
    [
      "a parameter annotation",
      "type Leg = { from: string }; function f({ from }: Pick<Leg, 'from'>) { return from; }",
    ],
  ] as const) {
    it(`flags ${name}`, () => {
      assert.equal(reports(code).length, 1);
    });
  }

  for (const [name, code] of [
    [
      "a package type",
      "import type { Rule } from 'eslint'; type A = Omit<Rule.RuleModule, 'meta'>;",
    ],
    ["a lib global", "type A = Pick<Location, 'hash'>;"],
    [
      "a type parameter",
      "function pick<T, K extends keyof T>(o: T): Pick<T, K> { return o; }",
    ],
    ["an inline literal", "type A = Pick<{ a: 1; b: 2 }, 'a'>;"],
    [
      "a local binding named Pick",
      "type Pick<T, K> = [T, K]; type Leg = {}; type A = Pick<Leg, 'x'>;",
    ],
  ] as const) {
    it(`leaves ${name} alone`, () => {
      assert.deepEqual(reports(code), []);
    });
  }

  it("names the target and the fix in its message", () => {
    const [message] = reports(
      "type Leg = { from: string }; type A = Pick<Leg, 'from'>;",
    );
    assert.match(message ?? "", /`Pick<Leg, …>`.*narrow type first/);
  });
});
