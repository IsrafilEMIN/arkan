import { setTimeout as delay } from "node:timers/promises";
import { parseArgs as parseArgv } from "node:util";
import {
  GhGitHubReader,
  WatcherQueryError,
  discoverStack,
  resolveContext,
} from "./github.ts";
import {
  runQueued,
  runSimple,
  statusQueryVerdict,
  verdictFactory,
  type WatchClock,
} from "./policy.ts";
import { renderJson, renderPretty } from "./render.ts";
import type * as T from "./types.ts";
import { nonEmpty, parsePrNumber } from "./types.ts";
export interface CliOptions {
  readonly owner: string | null;
  readonly repo: string | null;
  readonly pr: T.PrNumber | null;
  readonly mode: T.WatchMode;
  readonly stackPrs: readonly T.PrNumber[];
  readonly statusOnly: boolean;
  readonly pretty: boolean;
  readonly polling: T.PollingOptions;
}
class UsageError extends Error {
  constructor(readonly exitCode: 0 | 64) {
    super(`watch-pr argument parsing ended with exit ${exitCode}`);
  }
}
class InvalidArgumentError extends Error {}
function positiveNumber(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0)
    throw new InvalidArgumentError("must be greater than zero");
  return parsed;
}
function nonNegativeNumber(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0)
    throw new InvalidArgumentError("must be zero or greater");
  return parsed;
}
function positiveInteger(value: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0)
    throw new InvalidArgumentError("must be a positive integer");
  return parsed;
}
function prNumber(value: string): T.PrNumber {
  try {
    return parsePrNumber(Number(value.replace(/^#/, "")));
  } catch {
    throw new InvalidArgumentError("must be a positive integer");
  }
}
function stackPrList(value: string): T.NonEmpty<T.PrNumber> {
  const numbers = value.split(",").map((part) => prNumber(part.trim()));
  if (new Set(numbers).size !== numbers.length)
    throw new InvalidArgumentError("contains a duplicate PR");
  const parsed = nonEmpty(numbers);
  if (parsed === null) throw new InvalidArgumentError("cannot be empty");
  return parsed;
}
const HELP = `Usage: watch-pr [options]

Watch one pull request, a connected stack, or an immutable queued stack.
JSON (NDJSON while polling) is the default; --pretty renders human text.

Options:
  --owner <owner>             GitHub repository owner
  --repo <repo>               GitHub repository name
  --pr <number>               pull request number
  --stack                     watch the connected open stack (default: false)
  --queued-stack              watch the captured stack until all PRs merge
                              (default: false)
  --stack-prs <n,...>         frozen bottom-to-top queue (queued mode only)
  --interval <seconds>        poll interval (default: 60)
  --sweep-interval <seconds>  whole-stack sweep interval (default: 300)
  --timeout <seconds>         deadline; 0 disables it (default: 0)
  --max-query-errors <count>  consecutive query-error budget (default: 5)
  --status-only               print one status table and exit 0 (default:
                              false)
  --allow-draft               do not treat a draft as a merge gate (default:
                              false)
  --pretty                    render human text instead of JSON (default:
                              false)
  -h, --help                  display help for command
`;
const VALUE_FLAGS: Readonly<Record<string, string>> = {
  owner: "--owner <owner>",
  repo: "--repo <repo>",
  pr: "--pr <number>",
  "stack-prs": "--stack-prs <n,...>",
  interval: "--interval <seconds>",
  "sweep-interval": "--sweep-interval <seconds>",
  timeout: "--timeout <seconds>",
  "max-query-errors": "--max-query-errors <count>",
};
const BOOLEAN_FLAGS: readonly string[] = [
  "stack",
  "queued-stack",
  "status-only",
  "allow-draft",
  "pretty",
];
export function parseArgs(
  argv: readonly string[],
  io: Pick<CliRuntime, "stdout" | "stderr">
): CliOptions {
  const usageError = (message: string): UsageError => {
    io.stderr(`error: ${message}\n`);
    return new UsageError(64);
  };
  const { values, tokens } = parseArgv({
    args: [...argv],
    strict: false,
    allowPositionals: true,
    tokens: true,
    options: {
      ...Object.fromEntries(
        Object.keys(VALUE_FLAGS).map((name) => [name, { type: "string" as const }])
      ),
      ...Object.fromEntries(
        BOOLEAN_FLAGS.map((name) => [name, { type: "boolean" as const }])
      ),
      help: { type: "boolean", short: "h" },
    },
  });
  for (const token of tokens) {
    if (token.kind === "positional")
      throw usageError(
        `too many arguments. Expected 0 arguments but got ${argv.length}.`
      );
    if (token.kind !== "option") continue;
    const flags = VALUE_FLAGS[token.name];
    if (flags !== undefined) {
      if (token.value === undefined)
        throw usageError(`option '${flags}' argument missing`);
    } else if (token.name !== "help" && !BOOLEAN_FLAGS.includes(token.name)) {
      throw usageError(`unknown option '${token.rawName}'`);
    } else if (token.value !== undefined) {
      throw usageError(`unknown option '${token.rawName}=${token.value}'`);
    }
  }
  if (values.help === true) {
    io.stdout(HELP);
    throw new UsageError(0);
  }
  const value = <V>(name: string, parse: (raw: string) => V): V | undefined => {
    const raw = values[name];
    if (typeof raw !== "string") return undefined;
    try {
      return parse(raw);
    } catch (error) {
      if (!(error instanceof InvalidArgumentError)) throw error;
      throw usageError(
        `option '${VALUE_FLAGS[name]}' argument '${raw}' is invalid. ${error.message}`
      );
    }
  };
  const owner = value("owner", String);
  const repo = value("repo", String);
  const pr = value("pr", prNumber);
  const stackPrs = value("stack-prs", stackPrList);
  const interval = value("interval", positiveNumber) ?? 60;
  const sweepInterval = value("sweep-interval", positiveNumber) ?? 300;
  const timeout = value("timeout", nonNegativeNumber) ?? 0;
  const maxQueryErrors = value("max-query-errors", positiveInteger) ?? 5;
  const stack = values.stack === true;
  const queuedStack = values["queued-stack"] === true;
  if (stack && queuedStack)
    throw usageError(
      "option '--stack' cannot be used with option '--queued-stack'"
    );
  if (stackPrs !== undefined && !queuedStack)
    throw usageError("--stack-prs requires --queued-stack");
  return {
    owner: owner ?? null,
    repo: repo ?? null,
    pr: pr ?? null,
    mode: queuedStack ? "queued-stack" : stack ? "stack" : "single",
    stackPrs: stackPrs ?? [],
    statusOnly: values["status-only"] === true,
    pretty: values.pretty === true,
    polling: {
      interval,
      sweepInterval,
      timeout,
      maxQueryErrors,
      allowDraft: values["allow-draft"] === true,
    },
  };
}
export interface CliRuntime {
  readonly reader: T.GitHubReader;
  readonly clock: WatchClock;
  readonly stdout: (value: string) => void;
  readonly stderr: (value: string) => void;
}
function realRuntime(): CliRuntime {
  return {
    reader: new GhGitHubReader(),
    clock: {
      now: () => performance.now() / 1_000,
      observedAt: () => new Date().toISOString(),
      sleep: async (seconds) => {
        await delay(seconds * 1_000);
      },
    },
    stdout: (value) => process.stdout.write(value),
    stderr: (value) => process.stderr.write(value),
  };
}
export async function main(
  argv: readonly string[],
  runtime: CliRuntime = realRuntime()
): Promise<number> {
  let options: CliOptions;
  try {
    options = parseArgs(argv, runtime);
  } catch (error) {
    if (!(error instanceof UsageError)) throw error;
    return error.exitCode;
  }
  const render = options.pretty ? renderPretty : renderJson;
  const emit = (verdict: T.ProgressVerdict): void =>
    runtime.stdout(render(verdict));
  let contexts: T.NonEmpty<T.PrContext>;
  try {
    const seed = await resolveContext({
      reader: runtime.reader,
      owner: options.owner,
      repo: options.repo,
      pr: options.pr ?? options.stackPrs[0] ?? null,
    });
    contexts =
      nonEmpty(options.stackPrs.map((number) => ({ ...seed, number }))) ??
      (options.mode === "single"
        ? [seed]
        : await discoverStack(runtime.reader, seed));
  } catch (error) {
    if (!(error instanceof WatcherQueryError)) throw error;
    const verdict = statusQueryVerdict(
      verdictFactory(runtime.clock, options.mode),
      1,
      error.failure
    );
    runtime.stdout(render(verdict));
    return verdict.exitCode;
  }
  const dependencies = { reader: runtime.reader, clock: runtime.clock, emit };
  const verdict =
    options.mode === "queued-stack" && !options.statusOnly
      ? await runQueued({ dependencies, contexts, options: options.polling })
      : await runSimple({
          dependencies,
          contexts,
          mode: options.mode,
          statusOnly: options.statusOnly,
          options: options.polling,
        });
  runtime.stdout(render(verdict));
  return verdict.exitCode;
}
